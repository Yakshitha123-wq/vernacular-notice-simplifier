import base64
import json
import urllib.error
import urllib.request

import config


def extract_text(image_bytes):
    """OCR an image using Google Cloud Vision (DOCUMENT_TEXT_DETECTION).

    Raises RuntimeError if no key, no text found, or the API returns an error.
    """
    api_key = config.google_vision_api_key()
    if not api_key:
        raise RuntimeError("GOOGLE_VISION_API_KEY not configured")

    url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
    body = {
        "requests": [
            {
                "image": {"content": base64.b64encode(image_bytes).decode("ascii")},
                "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
            }
        ]
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Google Vision HTTP {exc.code}: {detail}")

    responses = data.get("responses") or []
    if not responses:
        raise RuntimeError("Google Vision returned no responses")

    response = responses[0]
    if "error" in response:
        raise RuntimeError(f"Google Vision error: {response['error']}")

    text = (response.get("fullTextAnnotation") or {}).get("text", "")
    if not text.strip():
        raise RuntimeError("Google Vision found no text")
    return text.strip()