#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-ap-south-1}"
SUFFIX="${1:-}"
STACK_NAME="${STACK_NAME:-notice-app-arnab}"
AUDIO_BUCKET="${AUDIO_BUCKET:-notice-audio-arnab}"
SOURCE_BUCKET="${SOURCE_BUCKET:-notice-uploads-arnab}"
MODEL_ID="${BEDROCK_MODEL_ID:-eu.anthropic.claude-sonnet-4-5-20250929-v1:0}"
BEDROCK_REGION="${BEDROCK_REGION:-eu-north-1}"
BEDROCK_REGIONS="${BEDROCK_REGIONS:-eu-north-1,eu-west-1,eu-central-1,eu-west-3,eu-south-1,eu-south-2}"
GROQ_MODEL="${GROQ_MODEL:-qwen/qwen3.8-27b}"
GROQ_VISION_MODEL="${GROQ_VISION_MODEL:-}"
GROQ_BASE_URL="${GROQ_BASE_URL:-https://api.groq.com/openai/v1}"
GROQ_MAX_TOKENS="${GROQ_MAX_TOKENS:-900}"
GROQ_API_KEY="${GROQ_API_KEY:-}"
GOOGLE_VISION_API_KEY="${GOOGLE_VISION_API_KEY:-}"

if [ -f "deploy/.groq.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "deploy/.groq.env"
  set +a
fi

if [ -z "$SUFFIX" ]; then
  SUFFIX="$(python3 - <<'EOF'
import random, string
print(''.join(random.choices(string.ascii_lowercase + string.digits, k=6)))
EOF
)"
fi

ARTIFACT_BUCKET="notice-deploy-${SUFFIX}"
PACKAGED="deploy/packaged-${SUFFIX}.yaml"
CODE_ZIP="deploy/src.zip"

echo "==> Packaging Lambda code"
rm -f "$CODE_ZIP"

DEPS_DIR="$(mktemp -d)"
TMPZ="$(mktemp -d)"
python3 -m pip download \
  -q --no-deps --only-binary=:all: \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 312 \
  --abi cp312 \
  -d "$DEPS_DIR" \
  numpy pillow edge-tts aiohttp aiohappyeyeballs aiosignal attrs frozenlist multidict propcache yarl idna certifi typing_extensions

cp -R src/* "$TMPZ"/
cp -R prompts "$TMPZ"/
(cd "$DEPS_DIR" && for w in *.whl; do unzip -qq -o "$w"; done && cp -R ./* "$TMPZ"/)

# Bundle Tesseract OCR binary + traineddata for Bengali/Telugu/Hindi/English
TESS_TMP="$(mktemp -d)"
curl -sL -o "$TESS_TMP/layer.zip" "https://github.com/bweigel/aws-lambda-tesseract-layer/releases/download/v5.4.0/tesseract-al2023-x86.zip"
(cd "$TESS_TMP" && unzip -qq layer.zip)
for lang in ben tel; do
  curl -sL -o "$TESS_TMP/tesseract/share/tessdata/${lang}.traineddata" "https://github.com/tesseract-ocr/tessdata_best/raw/main/${lang}.traineddata"
done
mv "$TESS_TMP" "$TMPZ/tesseract"

(cd "$TMPZ" && zip -qr "$OLDPWD/$CODE_ZIP" . -x "*.pyc" "*/__pycache__/*" ".DS_Store")
rm -rf "$DEPS_DIR" "$TMPZ"

echo "==> Ensuring artifact bucket s3://${ARTIFACT_BUCKET}"
aws s3 mb "s3://${ARTIFACT_BUCKET}" --region "$REGION" 2>/dev/null || true
aws s3 cp "$CODE_ZIP" "s3://${ARTIFACT_BUCKET}/src.zip" --region "$REGION"

echo "==> Generating packaged template"
sed "s|CodeUri: ../src|CodeUri: s3://${ARTIFACT_BUCKET}/src.zip|" deploy/template.yaml > "$PACKAGED"

echo "==> Deploying stack ${STACK_NAME}"
aws cloudformation deploy \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --template-file "$PACKAGED" \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    AudioBucketName="$AUDIO_BUCKET" \
    SourceBucketName="$SOURCE_BUCKET" \
    BedrockModelId="$MODEL_ID" \
    BedrockRegion="$BEDROCK_REGION" \
    BedrockRegions="$BEDROCK_REGIONS" \
    GroqApiKey="$GROQ_API_KEY" \
    GroqModel="$GROQ_MODEL" \
    GroqVisionModel="$GROQ_VISION_MODEL" \
    GroqBaseUrl="$GROQ_BASE_URL" \
    GroqMaxTokens="$GROQ_MAX_TOKENS" \
    GoogleVisionApiKey="$GOOGLE_VISION_API_KEY"

echo "==> Outputs:"
aws cloudformation describe-stacks \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs" \
  --output table