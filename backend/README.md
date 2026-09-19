# Vernacular Legal & Civic Notice Simplifier — Backend Pipeline

> This folder lives inside the monorepo at `vernacular-notice-simplifier/backend/`.

Live backend for the **First Commit** hackathon (WeMakeDevs Bharat Builds Tour, Sep 17–20 2026, Ship It track).

Takes a **photo or pasted text** of an official Bengali or Telugu civic or legal notice and returns:

- a plain-language simplified summary,
- structured action steps (what to do / what not to do),
- deadlines,
- target audience,
- a spoken audio version.

Team: Mannam (lead) · Padma & Mannam (frontend) · Arnab (+ Ujaan) — this repo is Arnab's backend slice.

## Live API

Base: `https://rcfb7kr4x0.execute-api.ap-south-1.amazonaws.com/prod`

| Method | Path | Body / Query | Returns |
|---|---|---|---|
| POST | `/get-upload-url` | `{"fileType":"image/png"}` or `{"filename","content_type"}` | `{upload_url, bucket, key, fileKey, uploadUrl, expires_in}` |
| POST | `/process-notice` | `{"text":"...","language":"bn"}` or `{"fileKey":"...","language":"bn"}` | flattened notice JSON (see below) |
| GET | `/notice/{id}` | — | stored notice |
| GET/POST | `/tts?language=bn&text=...` | query params | `audio/mpeg` MP3 |

Supported `language` codes: `bn` (Bengali), `te` (Telugu).

### Flattened response contract

```json
{
  "notice_id": "NOT-…",
  "language": "bn",
  "raw_text": "…",
  "category": "Tax/Fine",
  "simplified_summary": "…",
  "actionable_steps": ["…", "…"],
  "deadlines": ["2026-09-30"],
  "do_not_do": ["…"],
  "target_audience": "…",
  "audio_url": "https://…/notice-audio-arnab/…mp3" | null
}
```

## Architecture

```
Frontend (Amplify + React)
   │  POST /get-upload-url ──► presigned PUT to S3 (notice-uploads-arnab)
   ▼
API Gateway (ap-south-1) ──► Lambda (Python 3.12, 1024MB, 300s)
   ├── POST /process-notice  {text,language} or {fileKey,language}
   │     ├── Image (en)     → Amazon Textract OCR
   │     ├── Image (bn/te)  → bundled Tesseract OCR (ben/tel traineddata)
   │     └── Text           → passed straight through
   │
   │     Simplification:
   │       Bedrock Converse (Claude 4.5 / Nova) → strict-JSON simplification
   │       └─ multi-region failover: BEDROCK_REGIONS tried in order
   │       └─ Groq fallback (qwen/qwen3.8-27b) when Bedrock is unavailable
   │
   │     Audio:
   │       Edge TTS server-side (/tts) for bn/te
   │       Amazon Polly for English if configured
   │
   │     Storage:
   │       DynamoDB Notices table (NoticeID)
   │       S3 notice-audio-arnab (public-read audio MP3s)
   │
   ├── GET  /notice/{id}     fetch a stored notice
   ├── POST /get-upload-url  presigned S3 PUT (5 min)
   └── GET  /tts             MP3 synthesis for any supported language
```

## Local dev

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# Run tests
.venv/bin/python -m unittest tests.test_pipeline

# Live smoke test (hits deployed API; prints PASS/WARN per endpoint)
.venv/bin/python scripts/smoke_test.py
```

## Deploy

1. Make sure you have AWS credentials configured (`aws configure`).
2. Create `deploy/.groq.env` with the Groq key (this file is gitignored):

```bash
# deploy/.groq.env
GROQ_API_KEY=gsk_…
```

3. Run the deploy script:

```bash
./deploy/deploy.sh
```

This packages `src/`, `prompts/`, and all required native wheels (numpy, Pillow, edge-tts, Tesseract) into a zip, uploads it to S3, and runs `aws cloudformation deploy`.

To deploy to a different account or with different names:

```bash
AWS_PROFILE=mannam \
STACK_NAME=notice-app-team \
SOURCE_BUCKET=notice-uploads-team \
AUDIO_BUCKET=notice-audio-team \
BEDROCK_MODEL_ID=amazon.nova-lite-v1:0 \
./deploy/deploy.sh
```

## Configuration

| Env | Default | Meaning |
|---|---|---|
| `BEDROCK_MODEL_ID` | `eu.anthropic.claude-sonnet-4-5-20250929-v1:0` | Primary Bedrock model |
| `BEDROCK_REGION` | `eu-north-1` | Primary Bedrock region |
| `BEDROCK_REGIONS` | `eu-north-1,eu-west-1,eu-central-1,eu-west-3,eu-south-1,eu-south-2` | Failover order |
| `GROQ_API_KEY` | from `deploy/.groq.env` | Groq fallback API key |
| `GROQ_MODEL` | `qwen/qwen3.8-27b` | Groq fallback model |
| `GROQ_MAX_TOKENS` | `900` | Output-token cap for Groq OTPM quota |
| `VISION_FALLBACK` | `true` | Use bundled Tesseract when Textract fails/empty |
| `AWS_REGION` | `ap-south-1` | Region for Textract/Polly/S3/DDB |
| `SOURCE_BUCKET` / `AUDIO_BUCKET` | set at deploy | S3 buckets |

## Why AWS + why some tools are fallback-only

Our submission is **deployed on AWS**:

- **AWS Amplify** hosts the frontend.
- **API Gateway + Lambda + S3 + DynamoDB** run the backend.
- **Amazon Bedrock** is the *intended* LLM path (Claude 4.5 / Nova).
- **Amazon Textract** is the *intended* OCR path for English notices.
- **Amazon Polly** is the *intended* audio path for supported languages.

### Current constraints (account-level, not code-level)

1. **Bedrock paid-service activation is pending** on the primary team account. AWS returns `Operation not allowed`, `INVALID_PAYMENT_INSTRUMENT`, or `SubscriptionRequiredException`. We implemented **multi-region Bedrock failover** and a **Groq fallback** so the app works while AWS clears the account.
2. **Textract does not support Bengali/Telugu.** For bn/te photos we skip Textract and use an **open-source Tesseract OCR** binary bundled inside the Lambda — no extra signup/API key.
3. **Polly has no Bengali/Telugu voices.** For bn/te audio we use a bundled **Edge TTS** synthesizer inside the Lambda.
4. **Mannam's account** has Nova Bedrock working but still needs payment-method propagation + IAM deploy permissions for a team-wide deploy.

All of these are temporary AWS-account/billing gates; the code is ready to switch fully to Bedrock + Textract + Polly as soon as the account(s) are activated.

## Testing

```bash
.venv/bin/python -m unittest tests.test_pipeline
```

Current status: **35/35 tests pass**.

## Project context

See `CONTEXT.md` for the full day-by-day session log, decisions, and blockers.
