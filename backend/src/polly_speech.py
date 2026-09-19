import io
from uuid import uuid4

import config


def synthesize_audio(client, text, language, s3_client=None):
    voice_id = config.polly_voice(language)
    language_code = config.polly_language_code(language)
    response = client.synthesize_speech(
        OutputFormat="mp3",
        Text=text,
        VoiceId=voice_id,
        LanguageCode=language_code,
    )
    audio_stream = response.get("AudioStream")
    if audio_stream is None:
        raise RuntimeError("Polly returned no audio stream")
    audio_bytes = audio_stream.read()
    if s3_client is None:
        return audio_bytes
    bucket = config.audio_bucket()
    if not bucket:
        return audio_bytes
    key = f"audio/{uuid4().hex}.mp3"
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=audio_bytes,
        ContentType="audio/mpeg",
    )
    return key


def bucket_url(s3_client, key):
    bucket = config.audio_bucket()
    if not bucket:
        return None
    return f"https://{bucket}.s3.{config.region()}.amazonaws.com/{key}"