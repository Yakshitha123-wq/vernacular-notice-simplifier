# Vernacular Notice Simplifier — Project Writeup

## The problem

Official notices in India — from municipal corporations, landlords, tax offices, and government schemes — are often written in dense, formal language. For many people, especially older family members or those with limited schooling, these notices are hard to read even when they are in a familiar script.

Our app, **Notice, made simple**, takes a photo or pasted text of a Bengali or Telugu notice and returns:

- a plain-language summary,
- clear do-this / do-not-do action steps,
- key deadlines,
- target audience information,
- and a spoken audio version.

The goal is to help people understand what a notice actually means and what they need to do before the deadline passes.

## The build

The project is a mobile-first web app built over the First Commit hackathon weekend.

**Frontend:** React 19 + Vite + Tailwind CSS, hosted on AWS Amplify. The UI is intentionally simple: pick a language, share the notice, wait a few seconds, read or listen to the result.

**Backend:** A Python 3.12 Lambda function behind Amazon API Gateway. It exposes:
- `POST /get-upload-url` — presigned S3 PUT for image uploads,
- `POST /process-notice` — text or image simplification pipeline,
- `GET /notice/{id}` — retrieve a saved result,
- `GET /tts` — on-demand audio synthesis.

**Pipeline:**
- Images in English/Hindi go to Amazon Textract.
- Images in Bengali/Telugu use a bundled open-source Tesseract OCR binary, because Textract does not support those scripts.
- Extracted or pasted text is sent to Amazon Bedrock (Claude 4.5 / Nova) with a strict JSON prompt. The Lambda tries multiple Bedrock regions if the first fails.
- If Bedrock is unavailable, a Groq fallback provider handles simplification.
- Audio is generated with Microsoft Edge TTS inside Lambda for Bengali/Telugu, since Amazon Polly does not support those languages.
- Results are saved to DynamoDB and audio files are stored in a public S3 bucket.

**Resilience:** We hit several AWS account-level gates during the weekend (Bedrock `Operation not allowed`, Textract `SubscriptionRequiredException`, Claude `INVALID_PAYMENT_INSTRUMENT`). Rather than stop, we added region failover, provider fallback, and bundled open-source tools so the app would keep working end-to-end.

**Known limitation:** Because the live demo currently relies on the Groq fallback, rare outputs can include a stray foreign word or garbled phrase in one action step, even for identical input. We mitigated this by setting Groq's sampling temperature to 0 and adding a strict "respond only in the target language" rule to the prompt. The app performs most reliably on property-tax, ration-card, health-advisory, eviction, and traffic notices.

## Where AWS fits

AWS is the platform the app runs on:

- **AWS Amplify** hosts the frontend and auto-deploys from GitHub.
- **Amazon API Gateway + AWS Lambda** run the backend serverlessly.
- **Amazon S3** stores uploaded images and generated audio files.
- **Amazon DynamoDB** persists simplified notices.
- **Amazon Bedrock** is the intended LLM path for simplification.
- **Amazon Textract** is the intended OCR path for English/Hindi notices.
- **Amazon Polly** is ready for languages it supports.
- **AWS CloudFormation** deploys the entire backend stack.

The current fallback tools (Tesseract, Edge TTS, Groq) run inside AWS infrastructure and keep the app functional while AWS service activation finishes on our student accounts.

## Live links

- App: https://main.d1ikau4tnjl5sq.amplifyapp.com
- Source: https://github.com/Yakshitha123-wq/vernacular-notice-simplifier

## Team

Mannam (lead / frontend), Padma (frontend), Arnab Acharya (backend / pipeline), Ujaan Mukherjee (backend support / bug fixing).
