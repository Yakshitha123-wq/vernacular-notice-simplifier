import json
import re

import boto3

import config
import vision_ocr


def load_system_prompt(target_language):
    prompt_path = config_prompt_path()
    with open(prompt_path, "r", encoding="utf-8") as fh:
        template = fh.read()
    return template.replace("{TARGET_LANGUAGE}", target_language)


def transcribe_image_with_failover(image_bytes, target_language, image_format="jpeg"):
    last_error = None
    for region in config.bedrock_regions():
        client = boto3.client("bedrock-runtime", region_name=region)
        try:
            return vision_ocr.extract_text_from_image_bytes(
                client, image_bytes, target_language, image_format
            )
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"Image transcription failed in all regions: {last_error}")


def simplify_notice_with_failover(raw_text, target_language):
    last_error = None
    for region in config.bedrock_regions():
        client = boto3.client("bedrock-runtime", region_name=region)
        try:
            return simplify_notice(client, raw_text, target_language)
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"Bedrock invocation failed in all regions: {last_error}")


def simplify_notice_with_fallbacks(raw_text, target_language):
    try:
        return simplify_notice_with_failover(raw_text, target_language)
    except Exception as bedrock_error:
        if not config.groq_enabled():
            raise
        try:
            import llm_provider

            return llm_provider.simplify_notice(raw_text, target_language)
        except Exception as groq_error:
            raise RuntimeError(
                f"Bedrock ({bedrock_error}) and Groq fallback ({groq_error}) both failed"
            ) from groq_error


def transcribe_image_with_fallbacks(image_bytes, target_language, image_format="jpeg"):
    try:
        return transcribe_image_with_failover(image_bytes, target_language, image_format)
    except Exception as bedrock_error:
        if not config.groq_enabled():
            raise
        try:
            import llm_provider

            return llm_provider.transcribe_image(image_bytes, image_format)
        except Exception as groq_error:
            raise RuntimeError(
                f"Bedrock vision ({bedrock_error}) and Groq vision ({groq_error}) both failed"
            ) from groq_error


def simplify_notice(client, raw_text, target_language):
    response = client.converse(
        modelId=config.bedrock_model_id(),
        system=[{"text": _system_prompt(target_language)}],
        messages=[{"role": "user", "content": [{"text": _user_prompt(raw_text, target_language)}]}],
        inferenceConfig={"maxTokens": config.bedrock_max_tokens()},
    )
    output = response.get("output", {}).get("message", {})
    content = output.get("content") or []
    if not content:
        raise RuntimeError("Unexpected Bedrock response shape")
    text = content[0].get("text", "")
    if not text:
        raise RuntimeError("Bedrock returned empty assistant text")
    return parse_json_payload(text)


def _system_prompt(target_language):
    return load_system_prompt(target_language)


def _user_prompt(raw_text, target_language):
    language = config.language_name(target_language)
    return (
        f"Simplify this civic notice into plain, everyday {language}. "
        "Keep all dates and amounts exact. "
        "Return the response as JSON with fields: category, simplified_summary, "
        "actionable_steps, deadlines, target_audience.\n\n"
        'IMPORTANT: "deadlines" must be an array of plain date strings only, '
        'formatted like ["2026-09-30"] — do not return objects or extra fields '
        "inside deadlines. Never invent or complete a date: only include one if the "
        "notice states a complete day, month, and year. A recurring pattern with no "
        "year (e.g. \"every month on the 5th\") is not a deadline — leave it out of "
        "deadlines rather than turning it into a made-up calendar date.\n\n"
        f"IMPORTANT: Write every field entirely in {language}. Do not let any word "
        "from another language (English, Thai, or otherwise) slip into any single "
        "actionable_steps entry or any other field — only exact dates/amounts may "
        "stay as written.\n\n"
        f'Notice text: "{raw_text}"'
    )


_EXPECTED_KEYS = (
    "category",
    "simplified_summary",
    "actionable_steps",
    "deadlines",
    "target_audience",
    "do_not_do",
)


def parse_json_payload(text):
    text = text.strip()
    candidate = _try_parse(text)
    if candidate is None:
        fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
        if fenced:
            candidate = _try_parse(fenced.group(1).strip())
    if candidate is None:
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace > first_brace:
            candidate = _try_parse(text[first_brace : last_brace + 1])
    obj = _coerce_object(candidate)
    if obj is None:
        raise ValueError("Bedrock output did not contain valid JSON")
    return obj


def _try_parse(s):
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None


def _coerce_object(candidate):
    if isinstance(candidate, dict):
        if any(key in candidate for key in _EXPECTED_KEYS):
            return candidate
        nested = [v for v in candidate.values() if isinstance(v, dict)]
        if len(candidate) == 1 and len(nested) == 1:
            return _coerce_object(nested[0])
        return candidate
    if isinstance(candidate, list):
        for item in candidate:
            wrapped = _coerce_object(item)
            if wrapped is not None:
                return wrapped
    return None


def config_prompt_path():
    import config

    return config.prompt_file()