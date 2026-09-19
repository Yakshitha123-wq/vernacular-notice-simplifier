import os
import subprocess
import tempfile

import config

LANGUAGE_MAP = {
    "bn": "ben",
    "te": "tel",
    "hi": "hin",
    "en": "eng",
}


def _tesseract_cmd():
    return os.environ.get("TESSERACT_CMD") or config.env("TESSERACT_CMD", "/var/task/tesseract/bin/tesseract")


def _tessdata_prefix():
    return os.environ.get("TESSDATA_PREFIX") or config.env(
        "TESSDATA_PREFIX", "/var/task/tesseract/tesseract/share/tessdata"
    )


def _ld_library_path():
    libdir = os.environ.get("TESSERACT_LIB") or config.env("TESSERACT_LIB", "/var/task/tesseract/lib")
    current = os.environ.get("LD_LIBRARY_PATH", "")
    return f"{libdir}:{current}" if current else libdir


def extract_text(image_bytes, target_language="bn"):
    """OCR an image using the bundled Tesseract binary.

    Supports ben (Bengali), tel (Telugu), hin (Hindi), eng (English).
    Raises RuntimeError if no text is found or the binary fails.
    """
    lang_code = LANGUAGE_MAP.get((target_language or "bn").lower()[:2], "ben")
    cmd = _tesseract_cmd()
    if not os.path.exists(cmd):
        raise RuntimeError(f"Tesseract binary not found at {cmd}")

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as img_file:
        img_file.write(image_bytes)
        img_path = img_file.name

    try:
        env = os.environ.copy()
        env["TESSDATA_PREFIX"] = _tessdata_prefix()
        env["LD_LIBRARY_PATH"] = _ld_library_path()
        result = subprocess.run(
            [cmd, img_path, "stdout", "-l", lang_code, "--psm", "6", "--oem", "1"],
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
        )
        if result.returncode != 0:
            err = (result.stderr or "").strip() or "unknown error"
            raise RuntimeError(f"Tesseract failed: {err}")
        text = (result.stdout or "").strip()
        if not text:
            raise RuntimeError("Tesseract found no text")
        return text
    finally:
        try:
            os.unlink(img_path)
        except OSError:
            pass