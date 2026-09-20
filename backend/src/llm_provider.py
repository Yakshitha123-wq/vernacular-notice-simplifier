import base64
import json
import time
import urllib.error
import urllib.request

import config


def simplify_notice(raw_text, target_language):
    import bedrock_simplify

    messages = [
        {"role": "system", "content": bedrock_simplify.load_system_prompt(target_language)},
        {"role": "user", "content": bedrock_simplify._user_prompt(raw_text, target_language)},
    ]
    text = _chat_completion(messages, config.groq_model())
    return bedrock_simplify.parse_json_payload(text)


def transcribe_image(image_bytes, image_format="jpeg"):
    if not config.groq_vision_model():
        raise RuntimeError("GROQ_VISION_MODEL is not configured; no Groq vision backup")
    mime = _mime_for_format(image_format)
    data_url = f"data:{mime};base64,{base64.b64encode(image_bytes).decode('ascii')}"
    prompt = (
        "You are transcribing an official government notice captured in a photo for OCR."
        " Respond with ONLY the exact, verbatim text visible in the image. Do not translate,"
        " do not summarize, do not explain, and do not add any preamble."
        " Preserve the original language/script exactly as it appears."
    )
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }
    ]
    text = _chat_completion(messages, config.groq_vision_model())
    return text.strip()


class LlmError(RuntimeError):
    pass


def _chat_completion(messages, model):
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": config.groq_max_tokens(),
        "temperature": config.groq_temperature(),
    }
    api_key = config.groq_api_key()
    if not api_key:
        raise LlmError("GROQ_API_KEY is not configured")
    url = f"{config.groq_base_url().rstrip('/')}/chat/completions"
    body = json.dumps(payload).encode("utf-8")
    last_error = None
    for attempt in (1, 2):
        try:
            data = _post(url, body, api_key)
            content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
            return content
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            last_error = LlmError(f"Groq HTTP {exc.code}: {detail}")
            if exc.code < 500 and exc.code != 429:
                raise last_error
        except LlmError:
            raise
        except Exception as exc:
            last_error = LlmError(f"Groq request failed: {exc}")
        time.sleep(1.5 * attempt)
    raise RuntimeError(str(last_error))


def _post(url, body, api_key):
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
            ),
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=config.groq_timeout()) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _mime_for_format(image_format):
    return {
        "jpeg": "image/jpeg",
        "jpg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "bmp": "image/bmp",
    }.get((image_format or "jpeg").lower(), "image/jpeg")