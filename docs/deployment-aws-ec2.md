# GardnAIze — AWS EC2 low-cost deployment

This is a **single-host, cost-sensitive MVP** design, not a highly available production cluster. No AWS resources are provisioned by this PR. Deployment is disabled unless explicitly enabled in GitHub.

## Architecture

- One EC2 Linux instance, persistent EBS, Docker Engine + Docker Compose v2.24.4+, AWS CLI v2, SSM Agent.
- Frontend Nginx, Spring Boot, FastAPI, PostgreSQL 18 in Compose. **Only frontend bound to 127.0.0.1:8080**.
- A host-level reverse proxy (Caddy or Nginx) terminates HTTPS on ports 443/80 and proxies to `127.0.0.1:8080`; do not expose 8080, 8081, 8000 or 5432 publicly.
- PostgreSQL uses the persistent Compose volume on EBS. Back up the database consistently with `pg_dump` (or coordinated snapshots), test restores, and monitor disk usage.
- Amazon ECR holds three immutable SHA-tagged application images. PostgreSQL image remains upstream official; pin to a tested patch version/digest during release hardening.
- AWS Systems Manager Run Command invokes a **pre-installed script**; no inbound SSH and no GitHub-held EC2 SSH private key.
- AWS OIDC gives GitHub short-lived credentials; the EC2 instance profile pulls from ECR.

## One-time EC2 preparation (manual)

1. Provision EC2 in a suitable subnet, attach an encrypted persistent EBS volume, configure instance profile with `AmazonSSMManagedInstanceCore`, `AmazonEC2ContainerRegistryReadOnly` and permission for `sts:GetCallerIdentity` if required by policy. Ensure outbound connectivity to SSM/ECR (internet gateway or VPC endpoints). Use tight security groups (public HTTPS only, optional HTTP redirect). No public SSH required.
2. Install Docker Engine, Docker Compose v2.24.4+, AWS CLI v2, SSM Agent, curl and a reverse proxy with a valid TLS certificate.
3. Create `/opt/gardnaize` and install **the reviewed files** `compose.yaml`, `compose.aws.yaml` and `scripts/deploy-ec2.sh` (as `/opt/gardnaize/deploy.sh`, executable). **Update these files deliberately when the deployment configuration changes**; the GitHub workflow does not synchronize scripts to EC2.
4. Create `/opt/gardnaize/.env` owned by root and chmod 600. Include `DB_PASSWORD` (strong random password), `AWS_REGION` (e.g. `eu-west-3`), `VISION_ENABLED` (default false), and optionally `GEMINI_API_KEY`. Never commit or print credentials. Consider SSM Parameter Store SecureString / Secrets Manager for operational secret rotation. Do not use `POSTGRES_PASSWORD` instead of `DB_PASSWORD`.
5. Configure the host HTTPS reverse proxy to forward to `127.0.0.1:8080`. Validate TLS and external DNS separately. Do not serve the application publicly until photo consent/retention and backup policies are reviewed.
6. Create ECR repositories `gardnaize-frontend`, `gardnaize-backend`, `gardnaize-ai-service`. Enable scan-on-push and lifecycle retention rules as appropriate.
7. Create a **GitHub OIDC IAM role** restricted to this repository and the `main` branch (and appropriate audience). Its permissions: ECR push for the three repositories, `ssm:SendCommand` on **one specific instance** and the `AWS-RunShellScript` document, `ssm:GetCommandInvocation` for polling, and relevant read-only describe calls. Do not use long-lived AWS keys. Review IAM trust conditions and resource scope.

## GitHub configuration

Repository → Settings → Secrets and variables → Actions → **Variables**:

- `AWS_DEPLOY_ENABLED=true` — enables existing ECR image publishing on main after CI passes.
- `AWS_EC2_DEPLOY_ENABLED=true` — enables EC2 deployment **after** successful ECR publishing.
- `AWS_ROLE_ARN=arn:aws:iam::<account>:role/<oidc-role>`
- `AWS_REGION=eu-west-3` (or your chosen region).
- `AWS_EC2_INSTANCE_ID=i-...` (target instance).

Configure a GitHub **environment** named `ec2-production` with required reviewers if desired; the deployment job references it. Restrict it to `main`. Only enable the deployment after EC2 bootstrap, backups, secrets, IAM and HTTPS are verified.

## Release process

1. Merge a PR into `main`.
2. Existing CI builds/tests the application.
3. Existing `publish-ecr` job pushes images tagged with the immutable commit SHA.
4. New `deploy-ec2` job requests an SSM command on the configured instance.
5. EC2 `deploy.sh` logs in to ECR via the instance role, pulls the three SHA-tagged images, validates Compose and starts services with `--no-build --wait`, then checks the frontend locally.
6. GitHub waits for the SSM command and fails if it fails. A successful smoke check does **not** prove full end-to-end or external HTTPS readiness.

## Rollback and recovery

Run the same `/opt/gardnaize/deploy.sh <previous-known-good-40-char-SHA>` through SSM after ensuring images remain in ECR. Database migrations may be irreversible; take a database backup and review Flyway changes before deploying. For a failed deploy, inspect SSM command output and `docker compose logs` on the instance. Ensure the persistent database volume is not deleted during deployments.

## Cost and availability caveats

EC2 + EBS + ECR + minimal SSM typically avoids recurring ALB/RDS/NAT gateway charges for the first MVP, but the instance is a single point of failure. Costs also include IPv4, outbound data, snapshots, CloudWatch, storage and Gemini usage. Budget alerts and automatic backups are strongly recommended. Migrate to managed RDS and multi-instance services when usage or recovery objectives justify them.
