#!/usr/bin/env bash
# Install this script on the EC2 host at /opt/gardnaize/deploy.sh.
# Execute through AWS Systems Manager Run Command; no inbound SSH needed.
set -Eeuo pipefail
umask 077

IMAGE_TAG="${1:?Usage: deploy.sh <40-character-git-sha>}"
if [[ ! "$IMAGE_TAG" =~ ^[0-9a-f]{40}$ ]]; then
    echo "Invalid image tag; expected a full git commit SHA" >&2
    exit 2
fi

cd /opt/gardnaize
test -f .env || { echo "Missing /opt/gardnaize/.env" >&2; exit 1; }
set -a
# The .env file is managed locally by the administrator; never stored in Git.
source ./.env
set +a
: "${DB_PASSWORD:?DB_PASSWORD is required}"
: "${AWS_REGION:?AWS_REGION is required}"

AWS_ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
export ECR_REGISTRY IMAGE_TAG

aws ecr get-login-password --region "$AWS_REGION" |
    docker login --username AWS --password-stdin "$ECR_REGISTRY" >/dev/null

compose=(docker compose -f compose.yaml -f compose.aws.yaml)
"${compose[@]}" config --quiet
"${compose[@]}" pull frontend backend ai-service
"${compose[@]}" up --no-build -d --wait --wait-timeout 180

curl --fail --silent --show-error --max-time 15 http://127.0.0.1:8080/ >/dev/null
echo "Deployed image tag $IMAGE_TAG successfully"
