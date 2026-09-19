import os


def env(key, default=None):
    return os.environ.get(key, default)


def region():
    return env("AWS_REGION", "ap-south-1")


def notices_table():
    return env("NOTICES_TABLE", "Notices")


def audio_bucket():
    return env("AUDIO_BUCKET")


def source_bucket():
    return env("SOURCE_BUCKET")


def bedrock_model_id():
    return env(
        "BEDROCK_MODEL_ID",
        "eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
    )


def bedrock_region():
    return env("BEDROCK_REGION", "eu-north-1")


def bedrock_regions():
    raw = env("BEDROCK_REGIONS")
    if raw:
        return [r.strip() for r in raw.split(",") if r.strip()]
    return [bedrock_region()]


def bedrock_max_tokens():
    return int(env("BEDROCK_MAX_TOKENS", "2048"))


def google_vision_api_key():
    return env("GOOGLE_VISION_API_KEY", "")


def groq_api_key():
    return env("GROQ_API_KEY", "")


def groq_base_url():
    return env("GROQ_BASE_URL", "https://api.groq.com/openai/v1")


def groq_model():
    return env("GROQ_MODEL", "qwen/qwen3.8-27b")


def groq_vision_model():
    return env("GROQ_VISION_MODEL", "")


def groq_timeout():
    return float(env("GROQ_TIMEOUT", "30"))


def groq_max_tokens():
    return int(env("GROQ_MAX_TOKENS", "900"))


def groq_enabled():
    return bool(groq_api_key())


def language_name(language):
    names = {
        "bn": "Bengali",
        "te": "Telugu",
        "hi": "Hindi",
    }
    return names.get((language or "en").lower()[:2], "English")


def textract_use_async():
    return env("TEXTRACT_ASYNC", "false").lower() in ("1", "true", "yes")


def vision_fallback_enabled():
    return env("VISION_FALLBACK", "true").lower() not in ("0", "false", "no")


def polly_voice(language):
    voices = {
        "bn": env("POLLY_VOICE_BN", "Kajal"),
        "te": env("POLLY_VOICE_TE", "Shreya"),
        "hi": env("POLLY_VOICE_HI", "Aditi"),
    }
    return voices.get((language or "en").lower()[:2], env("POLLY_VOICE_DEFAULT", "Aditi"))


def polly_language_code(language):
    codes = {
        "bn": "bn-IN",
        "te": "te-IN",
        "hi": "hi-IN",
    }
    return codes.get((language or "en").lower()[:2], "hi-IN")


def prompt_file():
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, "prompts", "simplify_notice.txt"),
        os.path.join(os.path.dirname(here), "prompts", "simplify_notice.txt"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[1]