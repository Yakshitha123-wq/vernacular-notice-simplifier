import config


def extract_text_from_image_bytes(client, image_bytes, target_language="bn", image_format="jpeg"):
    prompt = (
        "You are transcribing an official government notice captured in a photo for OCR."
        " Respond with ONLY the exact, verbatim text visible in the image. Do not translate,"
        " do not summarize, do not explain, and do not add any preamble."
    )
    response = client.converse(
        modelId=config.bedrock_model_id(),
        messages=[
            {
                "role": "user",
                "content": [
                    {"image": {"format": image_format, "source": {"bytes": image_bytes}}},
                    {"text": prompt},
                ],
            }
        ],
        inferenceConfig={"maxTokens": config.bedrock_max_tokens()},
    )
    output = response.get("output", {}).get("message", {})
    content = output.get("content") or []
    if not content:
        raise RuntimeError("Unexpected Bedrock response shape during image transcription")
    text = content[0].get("text", "")
    if not text:
        raise RuntimeError("Bedrock returned empty transcription")
    return text.strip()


def sniff_image_format(image_bytes):
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if image_bytes[:3] == b"GIF":
        return "gif"
    if image_bytes[:2] == b"BM":
        return "bmp"
    if image_bytes[:2] == b"\xff\xd8":
        return "jpeg"
    if image_bytes[:4] == b"webp":
        return "webp"
    return "jpeg"