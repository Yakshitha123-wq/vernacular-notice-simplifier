# Vernacular Notice Simplifier — Frontend

Mobile-first web app that explains **Bengali, Telugu, and Hindi** civic/legal notices in plain language — and reads them aloud.

Built for **WeMakeDevs Bharat Builds Tour — First Commit** hackathon, Sep 17–20 2026.

- **Live demo:** https://main.d1ikau4tnjl5sq.amplifyapp.com/
- **Backend:** see the `backend/` folder in this repo
- **Live API:** `https://rcfb7kr4x0.execute-api.ap-south-1.amazonaws.com/prod`

## What it does

1. Choose a language: **বাংলা (Bengali) / తెలుగు (Telugu) / हिंदी (Hindi)**.
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

Create a local environment file:

```bash
cp .env.example .env.local
```

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
| **Amazon Textract** *(fallback)* | OCR for English/Hindi notice photos |
| **Amazon Bedrock** *(fallback)* | AI simplification when the AWS account has model access |

> The live backend currently uses a **Groq fallback** for simplification because the team's AWS account is still waiting for AWS verification / billing activation to invoke Bedrock reliably. All AWS infrastructure above is deployed and running; only the paid-model data-plane calls are gated by AWS account approval.

## Known limitations

- **Photo upload for Bengali/Telugu** depends on the backend OCR. Right now the frontend honestly tells users to *paste text* for bn/te because the backend's AWS Textract does not read those scripts, and our fallback OCR path is active only on the backend. The app still lets users try a photo if they prefer.
- **Audio generation** for bn/te is served by our backend's Edge-TTS route rather than Amazon Polly, because Polly does not offer Bengali/Telugu voices.
- **Backend account gates:** Bedrock/Textract paid-service access is pending AWS account verification on one team account. The fallback LLM keeps the app working while that clears.

## Team

- Mannam — team lead / frontend
- Padma — frontend
- Arnab — backend / AWS pipeline
- Ujaan — backend support
