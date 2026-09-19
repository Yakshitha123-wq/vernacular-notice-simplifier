#!/usr/bin/env python3
import base64
import json
import sys
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://rcfb7kr4x0.execute-api.ap-south-1.amazonaws.com/prod"

TINY_JPEG = base64.b64decode(
    "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a"
    "HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAA"
    "AAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AVN//2Q=="
)

PASS, FAIL, WARN = "PASS", "FAIL", "WARN"
results = []


def report(name, ok, message, status=None):
    tag = status or (PASS if ok else FAIL)
    results.append((name, tag, message))
    print(f"[{tag}] {name}: {message}")


def post(path, payload=None):
    req = urllib.request.Request(
        BASE + path,
        data=(json.dumps(payload or {}).encode("utf-8")),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(body)
        except ValueError:
            return exc.code, {"error": body[:200]}


def get(path):
    req = urllib.request.Request(BASE + path, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(body)
        except ValueError:
            return exc.code, {"error": body[:200]}


ACCOUNT_GATE_MARKERS = (
    "Operation not allowed",
    "SubscriptionRequiredException",
    "Your account is currently being verified",
    "needs a subscription for the service",
)


def classifies_as_account_gate(message):
    return any(m in message for m in ACCOUNT_GATE_MARKERS)


def main():
    print(f"Smoke test against {BASE}\n")

    status, data = post("/get-upload-url", {"filename": "notice.jpg", "content_type": "image/jpeg"})
    if status != 200:
        report("POST /get-upload-url", False, f"HTTP {status} {data}")
        sys.exit(1)
    upload_url = data["upload_url"]
    key = data["key"]
    report("POST /get-upload-url", True, f"bucket={data['bucket']} key={key}")

    req = urllib.request.Request(
        upload_url, data=TINY_JPEG, headers={"Content-Type": "image/jpeg"}, method="PUT"
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            report("PUT presigned upload", resp.status == 200, f"HTTP {resp.status}")
            if resp.status != 200:
                sys.exit(1)
    except urllib.error.HTTPError as exc:
        report("PUT presigned upload", False, f"HTTP {exc.code}")

    _, data = post("/process-notice", {"text": "কলকাতা পৌরসংস্থা। সম্পত্তি করের শেষ তারিখ ৩০ সেপ্টেম্বর ২০২৬।", "target_language": "bn"})
    if "error" in data and classifies_as_account_gate(data["error"]):
        report("POST /process-notice (text)", False, "ACCOUNT GATE: " + data["error"][:160], WARN)
    elif "simplified" in data:
        report("POST /process-notice (text)", True, "notice_id=" + data["notice_id"])
    else:
        report("POST /process-notice (text)", False, str(data)[:160])

    _, data = post("/process-notice", {"bucket": "notice-uploads-arnab", "key": key, "target_language": "bn"})
    if "error" in data and classifies_as_account_gate(data["error"]):
        report("POST /process-notice (S3 image)", False, "ACCOUNT GATE: " + data["error"][:160], WARN)
    elif "simplified" in data:
        report("POST /process-notice (S3 image)", True, "notice_id=" + data["notice_id"])
    else:
        report("POST /process-notice (S3 image)", False, str(data)[:160])

    status, data = get("/notice/NOT-SMOKE-TEST")
    if status in (200, 404) and (data.get("error") == "Notice not found" or "notice" not in data):
        report("GET /notice/NOT-SMOKE-TEST", True, "reachable, correctly says not found")
    else:
        report("GET /notice/NOT-SMOKE-TEST", False, f"HTTP {status} {data}")

    print("\n--- summary ---")
    any_warn = False
    for name, tag, _ in results:
        print(f"{tag:5s} {name}")
        if tag == WARN:
            any_warn = True
    print("\nIf WARN shows account-gate errors: AWS account is still activating for paid services")
    print("(Bedrock/Textract). Re-run this script once the account is active — no redeploy needed.")
    sys.exit(0 if not any_warn else 2)


if __name__ == "__main__":
    main()