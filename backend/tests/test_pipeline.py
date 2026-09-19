import io
import json
import os
import sys
import unittest
import urllib.request
from unittest import mock

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

os.environ.setdefault("AUDIO_BUCKET", "test-audio-bucket")
os.environ.setdefault("SOURCE_BUCKET", "test-source-bucket")

from PIL import Image, ImageDraw, ImageFont

import bedrock_simplify
import dynamo_store
import llm_provider
import preprocess
import vision_ocr
from handler import lambda_handler, _extract_from_remote


def make_notice_image(text="Notice about water supply."):
    font = None
    for name in ["DejaVuSans", "Arial", "Helvetica"]:
        try:
            font = ImageFont.truetype(name, 28)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()
    image = Image.new("RGB", (900, 500), "white")
    draw = ImageDraw.Draw(image)
    for i in range(4):
        draw.text((60, 60 + i * 80), text, fill="black", font=font)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


class PreprocessTest(unittest.TestCase):
    def test_returns_png_bytes(self):
        processed, original_format = preprocess.preprocess_image(make_notice_image())
        self.assertEqual(original_format, "JPEG")
        self.assertIsInstance(processed, bytes)
        reloaded = Image.open(io.BytesIO(processed))
        self.assertEqual(reloaded.format, "PNG")
        self.assertEqual(reloaded.mode, "L")

    def test_scales_large_images_down(self):
        large = Image.new("L", (5000, 3000), "white")
        buffer = io.BytesIO()
        large.save(buffer, format="PNG")
        processed, _ = preprocess.preprocess_image(buffer.getvalue())
        reloaded = Image.open(io.BytesIO(processed))
        self.assertLessEqual(max(reloaded.size), preprocess.MAX_DIMENSION)


class BedrockTest(unittest.TestCase):
    def test_system_prompt_embeds_language(self):
        prompt = bedrock_simplify.load_system_prompt("Telugu")
        self.assertIn("Telugu", prompt)
        self.assertNotIn("{TARGET_LANGUAGE}", prompt)

    def test_parse_json_plain(self):
        payload = '{"category": "Utility Outage", "deadlines": []}'
        self.assertEqual(bedrock_simplify.parse_json_payload(payload)["category"], "Utility Outage")

    def test_parse_json_fenced(self):
        payload = '```json\n{"category": "Tax/Fine", "deadlines": ["2026-09-30"]}\n```'
        result = bedrock_simplify.parse_json_payload(payload)
        self.assertEqual(result["deadlines"], ["2026-09-30"])

    def test_parse_json_embedded(self):
        payload = 'Sure, here you go: {"category": "Traffic", "actionable_steps": []} hope that helps.'
        result = bedrock_simplify.parse_json_payload(payload)
        self.assertEqual(result["category"], "Traffic")

    def test_parse_json_array_wrapper(self):
        payload = '[{"category": "Tax/Fine", "deadlines": ["2026-09-30"]}]'
        result = bedrock_simplify.parse_json_payload(payload)
        self.assertEqual(result["category"], "Tax/Fine")
        self.assertEqual(result["deadlines"], ["2026-09-30"])

    def test_parse_json_array_skips_scalar_then_dict(self):
        payload = '[null, "junk", {"category": "Ration", "target_audience": "all"}]'
        result = bedrock_simplify.parse_json_payload(payload)
        self.assertEqual(result["category"], "Ration")

    def test_parse_json_nested_single_key_unwrapped(self):
        payload = '{"result": {"category": "Water", "simplified_summary": "কাটা"}}'
        result = bedrock_simplify.parse_json_payload(payload)
        self.assertEqual(result["category"], "Water")

    def test_parse_json_bare_array_raises(self):
        with self.assertRaisesRegex(ValueError, "did not contain valid JSON"):
            bedrock_simplify.parse_json_payload("[1, 2, 3, 4]")

    def test_converse_call_shape_model_agnostic(self):
        client = mock.Mock()
        client.converse.return_value = {
            "output": {"message": {"content": [{"text": '{"category": "Tax/Fine", "deadlines": []}'}]}},
        }
        result = bedrock_simplify.simplify_notice(client, "কর দিনের শেষ তারিখ ৩০।", "bn")
        self.assertEqual(result["category"], "Tax/Fine")
        _, kwargs = client.converse.call_args
        self.assertIn("modelId", kwargs)
        self.assertTrue(kwargs["system"][0]["text"].startswith("You are a civic assistant"))
        self.assertEqual(kwargs["messages"][0]["role"], "user")
        self.assertIn("inferenceConfig", kwargs)


class PipelineTest(unittest.TestCase):
    def _fake_textract(self):
        client = mock.Mock()
        client.detect_document_text.return_value = {
            "Blocks": [{"BlockType": "LINE", "Text": "Water supply will stop on Friday."}]
        }
        return client

    def _fake_bedrock(self):
        client = mock.Mock()
        simplified = {
            "category": "Utility Outage",
            "original_language_guess": "bn",
            "simplified_summary": "পানি সরবরাহ বন্ধ থাকবে। আগে থেকে পানি জমা রাখুন।",
            "actionable_steps": ["পানি জমা রাখুন", "ট্যাংকার থেকে পানি নিন"],
            "do_not_do": [],
            "deadlines": [],
            "target_audience": "আবাসিক",
        }
        text = json.dumps(simplified, ensure_ascii=False)
        client.converse.return_value = {
            "output": {"message": {"role": "assistant", "content": [{"text": text}]}},
            "stopReason": "end_turn",
            "usage": {"totalTokens": 45},
        }
        return client

    def _fake_polly(self):
        client = mock.Mock()
        stream = io.BytesIO(b"fake-mp3-bytes")
        client.synthesize_speech.return_value = {"AudioStream": stream}
        return client

    @mock.patch("boto3.client")
    def test_get_upload_url(self, mock_boto):
        s3_client = mock.Mock()
        s3_client.generate_presigned_url.return_value = "https://presigned/..."
        mock_boto.return_value = s3_client
        event = {
            "httpMethod": "POST",
            "resource": "/get-upload-url",
            "body": json.dumps({"filename": "notice.jpg", "content_type": "image/jpeg"}),
        }
        result = lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 200)
        payload = json.loads(result["body"])
        self.assertIn("uploads/", payload["key"])
        self.assertEqual(payload["bucket"], "test-source-bucket")
        s3_client.generate_presigned_url.assert_called_once()

    def test_vision_ocr_extract_text(self):
        client = mock.Mock()
        client.converse.return_value = {
            "output": {"message": {"role": "assistant", "content": [{"text": "বাংলা পাঠ"}]}}
        }
        text = vision_ocr.extract_text_from_image_bytes(client, b"\xff\xd8fake", "bn", "jpeg")
        self.assertEqual(text, "বাংলা পাঠ")
        content = client.converse.call_args[1]["messages"][0]["content"]
        self.assertEqual(content[0]["image"]["source"]["bytes"], b"\xff\xd8fake")
        self.assertEqual(content[0]["image"]["format"], "jpeg")

    def test_sniff_image_format(self):
        self.assertEqual(vision_ocr.sniff_image_format(b"\x89PNG\r\n\x1a\nrest"), "png")
        self.assertEqual(vision_ocr.sniff_image_format(b"\xff\xd8rest"), "jpeg")
        self.assertEqual(vision_ocr.sniff_image_format(b"GIF89a"), "gif")

    @mock.patch.object(bedrock_simplify, "transcribe_image_with_failover")
    def test_vision_fallback_when_textract_empty(self, mock_transcribe):
        mock_transcribe.return_value = "ভিশন ফলব্যাক টেক্সট"
        sample = make_notice_image()
        s3 = mock.Mock()
        s3.download_file.side_effect = lambda b, k, p: open(p, "wb").write(sample)
        textract = mock.Mock()
        textract.detect_document_text.return_value = {"Blocks": []}
        out = _extract_from_remote(s3, textract, ("b", "photo.jpg"), "bn")
        self.assertEqual(out, "ভিশন ফলব্যাক টেক্সট")
        mock_transcribe.assert_called_once()

    @mock.patch.object(bedrock_simplify, "transcribe_image_with_failover")
    def test_vision_fallback_when_textract_errors(self, mock_transcribe):
        mock_transcribe.return_value = "ভিশন ফলব্যাক টেক্সট"
        sample = make_notice_image()
        s3 = mock.Mock()
        s3.download_file.side_effect = lambda b, k, p: open(p, "wb").write(sample)
        textract = mock.Mock()
        textract.detect_document_text.side_effect = RuntimeError(
            "SubscriptionRequiredException"
        )
        out = _extract_from_remote(s3, textract, ("b", "photo.jpg"), "bn")
        self.assertEqual(out, "ভিশন ফলব্যাক টেক্সট")
        mock_transcribe.assert_called_once()

    @mock.patch.object(bedrock_simplify, "transcribe_image_with_failover")
    def test_vision_fallback_skipped_when_textract_has_text(self, mock_transcribe):
        sample = make_notice_image()
        s3 = mock.Mock()
        s3.download_file.side_effect = lambda b, k, p: open(p, "wb").write(sample)
        textract = mock.Mock()
        textract.detect_document_text.return_value = {
            "Blocks": [{"BlockType": "LINE", "Text": "Water supply will stop on Friday."}]
        }
        out = _extract_from_remote(s3, textract, ("b", "photo.jpg"), "bn")
        self.assertEqual(out, "Water supply will stop on Friday.")
        mock_transcribe.assert_not_called()

    @mock.patch("boto3.client")
    def test_get_upload_url_filetype_alias(self, mock_boto):
        s3_client = mock.Mock()
        s3_client.generate_presigned_url.return_value = "https://presigned/..."
        mock_boto.return_value = s3_client
        event = {
            "httpMethod": "POST",
            "resource": "/get-upload-url",
            "body": json.dumps({"fileType": "image/png"}),
        }
        result = lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 200)
        payload = json.loads(result["body"])
        self.assertIn("uploadUrl", payload)
        self.assertIn("fileKey", payload)
        self.assertEqual(payload["uploadUrl"], payload["upload_url"])
        self.assertEqual(payload["fileKey"], payload["key"])
        _, kwargs = s3_client.generate_presigned_url.call_args
        self.assertEqual(kwargs["Params"]["ContentType"], "image/png")

    @mock.patch("boto3.client")
    def test_full_pipeline_api_event(self, mock_boto):
        s3_client = mock.Mock()
        mock_boto.side_effect = [
            s3_client,
            self._fake_textract(),
            self._fake_polly(),
            mock.Mock(),
            self._fake_bedrock(),
        ]
        event = {
            "body": json.dumps({
                "text": "পানি সরবরাহ শুক্রবার বন্ধ থাকবে।",
                "language": "bn",
            })
        }
        result = lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 200)
        payload = json.loads(result["body"])
        self.assertEqual(payload["simplified"]["category"], "Utility Outage")
        self.assertEqual(payload["category"], "Utility Outage")
        self.assertEqual(payload["simplified_summary"], "পানি সরবরাহ বন্ধ থাকবে। আগে থেকে পানি জমা রাখুন।")
        self.assertTrue(payload["notice_id"].startswith("NOT-"))
        self.assertIn("audio", payload["audio_url"])
        self.assertIsNotNone(payload["audio_url"])

    @mock.patch("boto3.client")
    def test_full_pipeline_filekey_language(self, mock_boto):
        s3_client = mock.Mock()
        sample = make_notice_image()

        def fake_download(bucket, key, path):
            with open(path, "wb") as fh:
                fh.write(sample)

        s3_client.download_file.side_effect = fake_download
        mock_boto.side_effect = [
            s3_client,
            self._fake_textract(),
            self._fake_polly(),
            mock.Mock(),
            self._fake_bedrock(),
        ]
        event = {
            "body": json.dumps({"fileKey": "uploads/some-notice.jpg", "language": "te"})
        }
        result = lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 200)
        payload = json.loads(result["body"])
        self.assertEqual(payload["language"], "te")
        self.assertIn("Water supply will stop", payload["raw_text"])
        s3_client.download_file.assert_called_once()

    @mock.patch("boto3.client")
    def test_full_pipeline_s3_event(self, mock_boto):
        s3_client = mock.Mock()
        sample_image = make_notice_image()

        def fake_download(bucket, key, path):
            with open(path, "wb") as fh:
                fh.write(sample_image)

        s3_client.download_file.side_effect = fake_download
        textract_client = self._fake_textract()
        bedrock_client = self._fake_bedrock()
        polly_client = self._fake_polly()
        mock_boto.side_effect = [
            s3_client,
            textract_client,
            polly_client,
            mock.Mock(),
            bedrock_client,
        ]
        event = {
            "Records": [{
                "eventSource": "aws:s3",
                "s3": {"bucket": {"name": "test-source-bucket"}, "object": {"key": "photo.jpg"}},
            }]
        }
        result = lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 200)
        payload = json.loads(result["body"])
        self.assertIn("Water supply will stop", payload["raw_text"])
        s3_client.download_file.assert_called_once()


class GroqFallbackTest(unittest.TestCase):
    def _with_groq_key(self):
        os.environ["GROQ_API_KEY"] = "test-groq-key"

    def _drop_groq_key(self):
        os.environ.pop("GROQ_API_KEY", None)

    def test_groq_simplify_notice(self):
        self._with_groq_key()
        try:
            payload = (
                '{"category": "Tax/Fine", "simplified_summary": "করে দিন", '
                '"actionable_steps": ["করে দিন"], "deadlines": ["2026-09-30"], '
                '"target_audience": "বাড়ির মালিক"}'
            )
            with mock.patch.object(llm_provider, "_chat_completion", return_value=payload) as call:
                result = llm_provider.simplify_notice("কর দিনের শেষ তারিখ ৩০।", "bn")
            self.assertEqual(result["category"], "Tax/Fine")
            self.assertEqual(result["deadlines"], ["2026-09-30"])
            messages = call.call_args[0][0]
            self.assertEqual(messages[0]["role"], "system")
            self.assertIn("plain date strings only", messages[1]["content"])
            self.assertIn("Bengali", messages[1]["content"])
        finally:
            self._drop_groq_key()

    def test_groq_transcribe_image(self):
        self._with_groq_key()
        try:
            os.environ["GROQ_VISION_MODEL"] = "tot-preview"
            try:
                with mock.patch.object(
                    llm_provider, "_chat_completion", return_value="বাংলা পাঠ"
                ) as call:
                    out = llm_provider.transcribe_image(b"\xff\xd8fake", "jpeg")
                self.assertEqual(out, "বাংলা পাঠ")
                content = call.call_args[0][0][0]["content"]
                self.assertTrue(any(item.get("type") == "image_url" for item in content))
            finally:
                os.environ.pop("GROQ_VISION_MODEL", None)
        finally:
            self._drop_groq_key()

    def test_groq_transcribe_image_disabled_without_vision_model(self):
        self._with_groq_key()
        try:
            with self.assertRaises(RuntimeError):
                llm_provider.transcribe_image(b"abc", "jpeg")
        finally:
            self._drop_groq_key()

    def test_simplify_falls_back_to_groq_when_bedrock_fails(self):
        self._with_groq_key()
        try:
            with mock.patch.object(
                bedrock_simplify,
                "simplify_notice_with_failover",
                side_effect=RuntimeError("Operation not allowed"),
            ):
                with mock.patch.object(
                    llm_provider, "simplify_notice", return_value={"category": "Tax/Fine"}
                ) as groq_call:
                    out = bedrock_simplify.simplify_notice_with_fallbacks("text", "bn")
            self.assertEqual(out["category"], "Tax/Fine")
            groq_call.assert_called_once()
        finally:
            self._drop_groq_key()

    def test_groq_skipped_when_bedrock_works(self):
        self._with_groq_key()
        try:
            with mock.patch.object(
                bedrock_simplify, "simplify_notice_with_failover", return_value={"category": "OK"}
            ):
                with mock.patch.object(
                    llm_provider, "simplify_notice", side_effect=AssertionError("should not call")
                ):
                    out = bedrock_simplify.simplify_notice_with_fallbacks("text", "bn")
            self.assertEqual(out["category"], "OK")
        finally:
            self._drop_groq_key()

    def test_no_groq_fallback_without_key(self):
        self._drop_groq_key()
        with mock.patch.object(
            bedrock_simplify,
            "simplify_notice_with_failover",
            side_effect=RuntimeError("Operation not allowed"),
        ):
            with self.assertRaises(RuntimeError):
                bedrock_simplify.simplify_notice_with_fallbacks("text", "bn")


class GoogleVisionOcrTest(unittest.TestCase):
    def test_extract_text_parses_response(self):
        import google_vision_ocr

        fake_response = {
            "responses": [
                {"fullTextAnnotation": {"text": "বাংলা পাঠ\nsecond line"}}
            ]
        }
        with mock.patch.object(
            urllib.request, "urlopen", return_value=io.BytesIO(json.dumps(fake_response).encode("utf-8"))
        ):
            with mock.patch.dict(os.environ, {"GOOGLE_VISION_API_KEY": "test-key"}):
                text = google_vision_ocr.extract_text(b"\xff\xd8fake-image")
        self.assertEqual(text, "বাংলা পাঠ\nsecond line")

    def test_extract_text_raises_on_api_error(self):
        import google_vision_ocr

        fake_response = {"responses": [{"error": {"message": "Bad image"}}]}
        with mock.patch.object(
            urllib.request, "urlopen", return_value=io.BytesIO(json.dumps(fake_response).encode("utf-8"))
        ):
            with mock.patch.dict(os.environ, {"GOOGLE_VISION_API_KEY": "test-key"}):
                with self.assertRaises(RuntimeError):
                    google_vision_ocr.extract_text(b"\xff\xd8fake")

    def test_extract_text_raises_without_key(self):
        import google_vision_ocr

        with mock.patch.dict(os.environ, {"GOOGLE_VISION_API_KEY": ""}, clear=False):
            with self.assertRaises(RuntimeError):
                google_vision_ocr.extract_text(b"\xff\xd8fake")


class TesseractOcrTest(unittest.TestCase):
    def test_extract_text_runs_tesseract_with_bengali(self):
        import tesseract_ocr

        fake_result = mock.Mock(returncode=0, stdout="বাংলা পাঠ\n", stderr="")
        with mock.patch.object(tesseract_ocr.subprocess, "run", return_value=fake_result) as run:
            with mock.patch.object(tesseract_ocr.os.path, "exists", return_value=True):
                with mock.patch.dict(os.environ, {"TESSERACT_CMD": "/fake/tesseract"}, clear=False):
                    text = tesseract_ocr.extract_text(b"\x89PNGfake", "bn")
        self.assertEqual(text, "বাংলা পাঠ")
        cmd = run.call_args[0][0]
        self.assertIn("ben", cmd)
        self.assertIn("--psm", cmd)
        self.assertIn("/fake/tesseract", cmd)

    def test_extract_text_raises_when_empty(self):
        import tesseract_ocr

        fake_result = mock.Mock(returncode=0, stdout="   ", stderr="")
        with mock.patch.object(tesseract_ocr.subprocess, "run", return_value=fake_result):
            with mock.patch.object(tesseract_ocr.os.path, "exists", return_value=True):
                with mock.patch.dict(os.environ, {"TESSERACT_CMD": "/fake/tesseract"}, clear=False):
                    with self.assertRaises(RuntimeError):
                        tesseract_ocr.extract_text(b"\x89PNGfake", "bn")


class DynamoStoreTest(unittest.TestCase):
    def test_save_notice_marshals_dynamodb_types(self):
        client = mock.Mock()
        dynamo_store.save_notice(client, "NOT-X", "raw", {"category": "Tax/Fine"}, "audio/k.mp3", "bn")
        item = client.put_item.call_args[1]["Item"]
        self.assertEqual(item["NoticeID"]["S"], "NOT-X")
        self.assertEqual(item["RawText"]["S"], "raw")
        self.assertEqual(item["AudioKey"]["S"], "audio/k.mp3")
        self.assertIn("Tax/Fine", item["SimplifiedJSON"]["S"])

    def test_save_notice_omits_audio_key_when_none(self):
        client = mock.Mock()
        dynamo_store.save_notice(client, "NOT-Y", "raw", {}, None, "bn")
        item = client.put_item.call_args[1]["Item"]
        self.assertNotIn("AudioKey", item)


class TtsRouteTest(unittest.TestCase):
    def test_get_tts_returns_binary_mp3(self):
        import base64
        import handler

        fake_provider = mock.Mock()
        fake_provider.synthesize.return_value = b"\xff\xfbbinary-mp3-bytes"
        event = {
            "resource": "/tts",
            "httpMethod": "GET",
            "queryStringParameters": {"language": "bn", "text": "সম্পত্তি কর দিন"},
            "body": "",
        }
        with mock.patch.dict(sys.modules, {"tts_provider": fake_provider}):
            # ensure the lazy import picks up our fake even if already imported
            sys.modules.pop("tts_provider", None)
            sys.modules["tts_provider"] = fake_provider
            response = handler.lambda_handler(event, {})
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(response["headers"]["Content-Type"], "audio/mpeg")
        self.assertTrue(response["isBase64Encoded"])
        self.assertEqual(base64.b64decode(response["body"]), b"\xff\xfbbinary-mp3-bytes")
        fake_provider.synthesize.assert_called_once_with("সম্পত্তি কর দিন", "bn")


if __name__ == "__main__":
    unittest.main(verbosity=2)