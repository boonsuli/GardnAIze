#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# GardnAIze - GDAI-VISION
# Gemini Vision API - Integration test
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

IMAGE="${GDAI_TEST_IMAGE:-$PROJECT_DIR/datasets/images/gemini_test/garden_gemini_test_01.png}"
MODEL="${GDAI_GEMINI_MODEL:-gemini-3.8-flash}"
API_VERSION="${GDAI_GEMINI_API_VERSION:-v1beta}"
API_BASE="https://generativelanguage.googleapis.com/$API_VERSION"

LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
RUN_ID="$(date +%Y%m%d_%H%M%S)_$$"
LOG_FILE="$LOG_DIR/gdai-vision-$RUN_ID.log"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

log() {
  printf '[%s] [%s] %s\n' \
    "$(date '+%Y-%m-%d %H:%M:%S')" "$1" "$2" \
    | tee -a "$LOG_FILE" >&2
}

info()  { log INFO "$1"; }
error() { log ERROR "$1"; }

# ------------------------------------------------------------
# 1. Prerequisites
# ------------------------------------------------------------

info "Starting GDAI-VISION Gemini test"
info "Project: $PROJECT_DIR"
info "Image: $IMAGE"
info "Model: $MODEL"
info "API version: $API_VERSION"

for cmd in curl jq base64; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    error "Missing command: $cmd"
    exit 1
  fi
done

if [[ ! -f "$IMAGE" ]]; then
  error "Image not found: $IMAGE"
  exit 1
fi

if [[ -z "${GEMINI_API_KEY:-}" ]]; then
  error "GEMINI_API_KEY is not defined"
  exit 1
fi

case "${IMAGE,,}" in
  *.png)  MIME_TYPE="image/png" ;;
  *.jpg|*.jpeg) MIME_TYPE="image/jpeg" ;;
  *.webp) MIME_TYPE="image/webp" ;;
  *)
    error "Unsupported image format"
    exit 1
    ;;
esac

info "Image size: $(du -h "$IMAGE" | cut -f1)"
info "MIME type: $MIME_TYPE"

# ------------------------------------------------------------
# 2. Build JSON request
# ------------------------------------------------------------

info "Encoding image in Base64"

base64 -w 0 "$IMAGE" > "$TMP_DIR/image.b64"

jq -n \
  --rawfile image "$TMP_DIR/image.b64" \
  --arg mime "$MIME_TYPE" \
  '{
    contents: [{
      parts: [
        {
          inline_data: {
            mime_type: $mime,
            data: $image
          }
        },
        {
          text: "Analyze this image for GardnAIze. Determine whether it represents a usable garden. Identify visible elements such as lawn, trees, terrace, fence and vegetation. Do not infer invisible attributes such as soil type, climate or daily sunlight exposure. Return a JSON object with isGarden, isUsable, gardenElements, visibleConditions and warnings."
        }
      ]
    }],
    generationConfig: {
      responseMimeType: "application/json"
    }
  }' > "$TMP_DIR/request.json"

info "Request JSON generated"


# ------------------------------------------------------------
# 3. Call Gemini API with automatic retries
# ------------------------------------------------------------

URL="$API_BASE/models/$MODEL:generateContent"

MAX_ATTEMPTS=4
HTTP_CODE="000"

for ((attempt=1; attempt<=MAX_ATTEMPTS; attempt++)); do

  info "Gemini request - attempt $attempt/$MAX_ATTEMPTS"

  START_TIME=$SECONDS

  HTTP_CODE=$(curl -sS \
    --connect-timeout 15 \
    --max-time 120 \
    -o "$TMP_DIR/response.json" \
    -w "%{http_code}" \
    -X POST "$URL" \
    -H "x-goog-api-key: $GEMINI_API_KEY" \
    -H "Content-Type: application/json" \
    --data-binary @"$TMP_DIR/request.json") || HTTP_CODE="000"

  ELAPSED=$((SECONDS - START_TIME))

  info "HTTP: $HTTP_CODE - Duration: ${ELAPSED}s"

  if [[ "$HTTP_CODE" == "200" ]]; then
    info "Gemini request successful"
    break
  fi

  # Retry only temporary server errors
  case "$HTTP_CODE" in
    408|500|502|503|504)
      if (( attempt < MAX_ATTEMPTS )); then
        DELAY=$((5 * 2 ** (attempt - 1) + RANDOM % 3))
        info "Temporary error. Retrying in ${DELAY}s"
        sleep "$DELAY"
      fi
      ;;
    *)
      error "Non-retryable error: HTTP $HTTP_CODE"
      break
      ;;
  esac
done

info "Final HTTP status: $HTTP_CODE"

# ------------------------------------------------------------
# 4. Handle API errors
# ------------------------------------------------------------

if [[ "$HTTP_CODE" != "200" ]]; then
  error "Gemini API returned HTTP $HTTP_CODE"

  jq -r \
    '.error.message // .error // "Unknown API error"' \
    "$TMP_DIR/response.json" 2>/dev/null \
    || cat "$TMP_DIR/response.json"

  if [[ "$HTTP_CODE" == "404" ]]; then
    info "Checking available Gemini models"

    MODELS_HTTP=$(curl -sS \
      --connect-timeout 15 \
      --max-time 30 \
      -o "$TMP_DIR/models.json" \
      -w "%{http_code}" \
      "$API_BASE/models" \
      -H "x-goog-api-key: $GEMINI_API_KEY") || {
        error "Unable to retrieve available models"
        exit 1
      }

    if [[ "$MODELS_HTTP" == "200" ]]; then
      info "Models supporting generateContent:"

      jq -r '
        .models[]
        | select(
            .supportedGenerationMethods // []
            | index("generateContent")
          )
        | .name
      ' "$TMP_DIR/models.json"
    else
      error "Model listing failed: HTTP $MODELS_HTTP"
      jq -r '.error.message // empty' \
        "$TMP_DIR/models.json" 2>/dev/null || true
    fi
  fi

  exit 1
fi

# ------------------------------------------------------------
# 5. Extract Gemini analysis
# ------------------------------------------------------------

info "Gemini API call successful"

ANALYSIS_FILE="$LOG_DIR/gdai-vision-$RUN_ID-analysis.json"

if ! jq -e -r \
  '.candidates[0].content.parts
   | map(.text // empty)
   | join("\n")
   | select(length > 0)' \
  "$TMP_DIR/response.json" > "$TMP_DIR/analysis.txt"; then
  error "No text returned by Gemini"
  exit 1
fi

if ! jq -e . "$TMP_DIR/analysis.txt" > "$ANALYSIS_FILE"; then
  error "Gemini response is not valid JSON"
  cat "$TMP_DIR/analysis.txt"
  exit 1
fi

info "Analysis saved: $ANALYSIS_FILE"
info "GDAI-VISION test completed successfully"

echo
echo "========== GDAI-VISION RESULT =========="
jq . "$ANALYSIS_FILE"
echo "========================================"
