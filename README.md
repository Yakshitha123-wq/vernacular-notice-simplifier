# Vernacular Notice Simplifier

Mobile-first web app that explains **Bengali and Telugu** civic/legal notices in plain language — and reads them aloud.

Built for **WeMakeDevs Bharat Builds Tour — First Commit** hackathon, Sep 17–20 2026.

- **Live app:** https://main.d1ikau4tnjl5sq.amplifyapp.com/
- **Source:** https://github.com/Yakshitha123-wq/vernacular-notice-simplifier
- **Live API:** `https://rcfb7kr4x0.execute-api.ap-south-1.amazonaws.com/prod`
- **Team writeup:** [`FirstCommit_writeup.md`](./FirstCommit_writeup.md)
- **Blog (Best Blog track):** https://builder.aws.com/content/3JZzl9VBUolKkJ1ybEo4IXlPpTi/notice-made-simple

## What it does

1. Choose a language: **বাংলা (Bengali) / తెలుగు (Telugu)**.
2. Upload a notice photo **or paste the notice text**.
3. Get a simple summary:
   - What kind of notice it is
   - What you should do
   - What you must **not** do
   - Deadlines
   - Who the notice is for
4. Tap **Play** to hear the simplified notice read aloud.

## Tech stack

- Vite + React 19
- Tailwind CSS 4
- Lucide icons
- AWS Amplify (hosting)
- AWS API Gateway + Lambda (backend)

## Run locally

```bash
cd vernacular-notice-simplifier
npm install
```

Create a local environment file from the example:

```bash
cp .env.example .env.local
```

`.env.local` is gitignored. The production build falls back to the live API URL in `src/lib/api.js`, so the deployed app does not depend on this file.

Then start the dev server:

```bash
npm run dev
```

Open the URL shown (usually `http://localhost:5179/`).

## Environment variables

| Variable | Example | Meaning |
|---|---|---|
| `VITE_API_BASE` | `https://rcfb7kr4x0.execute-api.ap-south-1.amazonaws.com/prod` | Base URL of the backend API |

Only `VITE_API_BASE` is required. No AWS credentials or API keys are stored in the frontend.

## Build

```bash
npm run build
```

Amplify auto-deploys when `main` is pushed to GitHub.

## How AWS is used

| AWS service | What it does in our app |
|---|---|
| **AWS Amplify** | Hosts the React frontend and auto-deploys from GitHub |
| **Amazon API Gateway** | Exposes the backend REST endpoints to the browser |
| **AWS Lambda** | Runs the Python backend that OCRs, simplifies, and stores notices |
| **Amazon S3** | Stores uploaded notice images and generated MP3 audio files |
| **Amazon DynamoDB** | Saves simplified notices so they can be fetched again by ID |
| **Amazon Textract** *(intended)* | OCR for English/Hindi notice photos once account access is active |
| **Amazon Bedrock** *(intended)* | AI simplification once model access is active on the team account |

### Current working path

The live backend currently uses:
- **Groq** (Qwen) for text simplification,
- **Tesseract** (bundled in Lambda) for Bengali/Telugu OCR,
- **Microsoft Edge TTS** for Bengali/Telugu audio,
- all running inside the **AWS Lambda / API Gateway** infrastructure.

This fallback keeps the app working end-to-end while the team's AWS account finishes verification / billing activation for Bedrock and Textract.

## Known limitations

- **Photo upload for Bengali/Telugu** uses bundled Tesseract OCR inside Lambda. It works, but accuracy depends on image quality.
- **Audio generation** for bn/te is served by the backend's Edge-TTS route rather than Amazon Polly, because Polly does not offer Bengali/Telugu voices.
- **Backend account gates:** Bedrock and Textract paid-service access is pending AWS account verification. The fallback LLM/OCR/audio stack keeps the app working while that clears.
- **Fallback generation variability:** The Groq fallback can occasionally insert a stray foreign word or garbled phrase into one action step, even when the same input is repeated. We have lowered the sampling temperature to 0 and tightened the prompt to reduce this. Results are best for property-tax, ration-card, health-advisory, eviction, and traffic notices.

## Team

- Mannam Yakshitha — team lead / frontend
- Padma — frontend
- Arnab — backend / AWS pipeline
- Ujaan — backend support

