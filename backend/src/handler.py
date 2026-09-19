import base64
import json
import os
import tempfile

import boto3

import bedrock_simplify
import config
import dynamo_store
import polly_speech
import preprocess
import textract_ocr


def lambda_handler(event, context):
    try:
        record = _first_record(event)
        if record and record.get("eventSource") == "aws:s3":
            result = _process_s3_event(record)
        else:
            result = _process_api_event(event)
        if isinstance(result, dict) and "statusCode" in result:
            return result
        return _ok(result)
    except Exception as exc:
        return _error(str(exc))


def _first_record(event):
    records = event.get("Records") or []
    return records[0] if records else None


def _process_api_event(event):
    body = json.loads(event.get("body") or "{}")
    resource = event.get("resource") or event.get("path") or ""
    if resource.rstrip("/").endswith("/get-upload-url") and event.get("httpMethod") == "POST":
        return _get_upload_url(body)
    if resource.rstrip("/").endswith("/tts"):
        return _get_tts(body, event.get("queryStringParameters") or {})
    if "text" in body and body.get("text"):
        return _run_pipeline(
            raw_text=body["text"],
            target_language=_target_language(body),
        )
    bucket = body.get("bucket") or config.source_bucket()
    key = body.get("key") or body.get("fileKey")
    if bucket and key:
        return _run_pipeline(remote=(bucket, key), target_language=_target_language(body))
    if "requestContext" in event and event.get("httpMethod") == "GET":
        return _get_notice(event.get("pathParameters") or {})
    raise ValueError("No text or S3 location provided")


def _target_language(body):
    return body.get("target_language") or body.get("language") or "bn"


def _get_upload_url(body):
    import uuid

    s3 = boto3.client("s3", region_name=config.region())
    bucket = config.source_bucket()
    if not bucket:
        raise ValueError("SOURCE_BUCKET not configured")
    content_type = (
        body.get("content_type")
        or body.get("contentType")
        or body.get("fileType")
        or "image/jpeg"
    )
    if not any(
        content_type.startswith(p) for p in ("image/jpeg", "image/png", "image/webp")
    ):
        content_type = "image/jpeg"
    ext = {"image/png": "png", "image/webp": "webp"}.get(content_type, "jpg")
    filename = (body.get("filename") or "").strip() or f"upload.{ext}"
    if filename.rsplit(".", 1)[-1].lower() not in {"jpg", "jpeg", "png", "webp"}:
        filename = f"upload.{ext}"
    key = f"uploads/{uuid.uuid4().hex}-{filename.replace(' ', '_')}"
    upload_url = s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": key, "ContentType": content_type},
        ExpiresIn=300,
    )
    return {
        "upload_url": upload_url,
        "uploadUrl": upload_url,
        "bucket": bucket,
        "key": key,
        "fileKey": key,
        "expires_in": 300,
    }


def _get_tts(body, query):
    import tts_provider

    text = body.get("text") or query.get("text") or ""
    language = (
        body.get("language")
        or body.get("target_language")
        or query.get("language")
        or query.get("lang")
        or "bn"
    )
    audio = tts_provider.synthesize(text, language)
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "audio/mpeg",
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=86400",
            "Content-Length": str(len(audio)),
        },
        "body": base64.b64encode(audio).decode("ascii"),
        "isBase64Encoded": True,
    }


def _process_s3_event(record):
    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]
    return _run_pipeline(remote=(bucket, key), target_language="bn")


def _run_pipeline(raw_text=None, remote=None, target_language="bn"):
    s3 = boto3.client("s3", region_name=config.region())
    textract = boto3.client("textract", region_name=config.region())
    polly = boto3.client("polly", region_name=config.region())
    dynamodb = boto3.client("dynamodb", region_name=config.region())

    if raw_text is None:
        raw_text = _extract_from_remote(s3, textract, remote, target_language)

    simplified = bedrock_simplify.simplify_notice_with_fallbacks(raw_text, target_language)

    audio_key = None
    audio_url = None
    try:
        summary_text = simplified.get("simplified_summary") or raw_text
        audio_key = polly_speech.synthesize_audio(polly, summary_text, target_language, s3)
        audio_url = polly_speech.bucket_url(s3, audio_key)
    except Exception as exc:
        print(f"[warn] audio synthesis skipped: {exc}")

    notice_id = dynamo_store.new_notice_id()
    dynamo_store.save_notice(dynamodb, notice_id, raw_text, simplified, audio_key, target_language)

    return {
        "notice_id": notice_id,
        "language": target_language,
        "raw_text": raw_text,
        "simplified": simplified,
        "category": simplified.get("category"),
        "simplified_summary": simplified.get("simplified_summary"),
        "actionable_steps": simplified.get("actionable_steps") or [],
        "deadlines": simplified.get("deadlines") or [],
        "do_not_do": simplified.get("do_not_do") or [],
        "target_audience": simplified.get("target_audience"),
        "audio_url": audio_url,
    }


def _extract_from_remote(s3, textract, remote, target_language="bn"):
    bucket, key = remote
    if _is_image_key(key):
        with tempfile.NamedTemporaryFile(delete=False) as raw_file:
            s3.download_file(bucket, key, raw_file.name)
            with open(raw_file.name, "rb") as fh:
                image_bytes = fh.read()
            os.unlink(raw_file.name)
        processed_bytes, _ = preprocess.preprocess_image(image_bytes)
        # Textract does not support Bengali/Telugu; use Tesseract directly for those.
        if target_language in ("bn", "te"):
            raw_text = ""
        else:
            try:
                raw_text = textract_ocr.extract_text(textract, image_bytes=processed_bytes)
            except Exception:
                if not config.vision_fallback_enabled():
                    raise
                raw_text = ""
        if not raw_text.strip() and config.vision_fallback_enabled():
            # 1) Try bundled Tesseract for Indic scripts (no external signup)
            try:
                import tesseract_ocr

                raw_text = tesseract_ocr.extract_text(image_bytes, target_language)
            except Exception as exc:
                print(f"[warn] Tesseract OCR failed: {exc}")
            # 2) Optional Google Cloud Vision if key is configured
            if not raw_text.strip() and config.google_vision_api_key():
                try:
                    import google_vision_ocr

                    raw_text = google_vision_ocr.extract_text(image_bytes)
                except Exception as exc:
                    print(f"[warn] Google Vision OCR failed: {exc}")
            # 3) Last resort: Bedrock/Groq vision fallback
            if not raw_text.strip():
                import vision_ocr

                raw_text = bedrock_simplify.transcribe_image_with_fallbacks(
                    image_bytes,
                    target_language,
                    vision_ocr.sniff_image_format(image_bytes),
                )
        return raw_text
    return textract_ocr.extract_text(textract, bucket=bucket, key=key)


def _is_image_key(key):
    ext = key.rsplit(".", 1)[-1].lower()
    return ext in {"jpg", "jpeg", "png", "bmp", "tif", "tiff", "webp", "heic"}


def _get_notice(path_parameters):
    dynamodb = boto3.client("dynamodb", region_name=config.region())
    notice_id = (path_parameters or {}).get("id")
    if not notice_id:
        raise ValueError("Missing notice id")
    item = dynamo_store.get_notice(dynamodb, notice_id)
    if item is None:
        return {"error": "Notice not found"}
    return item


def _ok(payload):
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(payload, ensure_ascii=False),
    }


def _error(message):
    return {
        "statusCode": 500,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps({"error": message}, ensure_ascii=False),
    }