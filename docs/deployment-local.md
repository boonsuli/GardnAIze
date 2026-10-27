# GardnAIze — local deployment modes

The repository supports **two alternative local modes**. Do not start both on the same ports. `compose.yaml` is the existing canonical stack; `compose.local.yaml` only overrides local settings.

## Mode A — Docker Compose (recommended for reproducible demos)

Prerequisites: Docker Compose v2.24.4+ (supports `!override`). From repository root:

```bash
cp .env.example .env
# Edit .env and set DB_PASSWORD (used by Compose); optional GEMINI_API_KEY.
docker compose -f compose.yaml -f compose.local.yaml config --quiet
docker compose -f compose.yaml -f compose.local.yaml up --build -d --wait
docker compose -f compose.yaml -f compose.local.yaml ps
```

- Frontend: http://localhost:8080
- Spring Boot: http://localhost:8081/actuator/health
- FastAPI: http://localhost:8000/health
- PostgreSQL: localhost:5432 (local-only, override with DB_PORT).

```bash
docker compose -f compose.yaml -f compose.local.yaml logs -f
docker compose -f compose.yaml -f compose.local.yaml down
```

PostgreSQL persists in a named volume. **Do not use `down -v` unless intentionally deleting all local data.** The Nginx container proxies `/api` to Spring Boot. `VISION_ENABLED` defaults to false; enable only after configuring Gemini and reviewing photo consent.

## Mode B — native, without Docker

Prerequisites: PostgreSQL 18, Java 25, Maven 3.9+, Python 3.12, Node.js 22.12+, npm 11. Start PostgreSQL and create the database/role once as a PostgreSQL administrator:

```sql
CREATE ROLE gardnaize LOGIN PASSWORD 'choose-a-local-password';
CREATE DATABASE gardnaize OWNER gardnaize;
```

Open three terminals. **Terminal 1: FastAPI**

```bash
cd ai-service
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Optional: export GEMINI_API_KEY=... (never commit keys)
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2: Spring Boot**

```bash
cd backend
export DB_URL="jdbc:postgresql://localhost:5432/gardnaize"
export DB_USER="gardnaize"
export DB_PASSWORD="choose-a-local-password"
export AI_BASE_URL="http://localhost:8000"
export VISION_BASE_URL="http://localhost:8000"
export VISION_PROVIDER_NAME="gemini-adapter"
export VISION_ENABLED="false"
export CORS_ALLOWED_ORIGIN="http://localhost:4200"
mvn spring-boot:run
```

Flyway migrations execute on backend startup. **Terminal 3: Angular**

```bash
cd frontend
npm install
npm start -- --host 127.0.0.1 --port 4200 --proxy-config proxy.conf.json
```

Open http://localhost:4200. The existing Angular proxy forwards `/api` to port 8081. Native mode is intended for debugging, not public hosting. For Windows PowerShell use `.venv\Scripts\Activate.ps1` and `$env:NAME="value"`; WSL2 supports the Linux commands.

## Checks and troubleshooting

```bash
curl --fail http://localhost:8000/health
curl --fail http://localhost:8081/actuator/health
```

Port collision: stop the other mode. Database error: check PostgreSQL service, user/password and migrations. CORS: match frontend origin or use Angular proxy. No Gemini key: vision calls will not work. Keep keys and private photos out of Git.

## AWS: cost-conscious deployment strategy

| Stage | Architecture | Main tradeoff |
| --- | --- | --- |
| Local development / Alyra demo | Docker Compose or native | Minimal cloud spend, reproducible |
| Hosted low-traffic MVP | **Single EC2 Linux VM + Docker Compose + persistent EBS** | Predictable baseline cost; self-managed VM, DB and backups |
| Moderate traffic | Angular on S3/CloudFront, API containers on EC2 or ECS/EC2, database on RDS if justified | Separate scaling and improved managed persistence |
| Growth / higher availability | ECS Fargate, ALB, RDS, S3/CloudFront | Lower operations overhead, but more fixed monthly infrastructure costs |

**Recommendation:** start with EC2 + Compose for the cost-sensitive public MVP, not a multi-AZ Fargate/ALB/RDS/NAT design. Protect the instance with HTTPS, firewall/security groups, least-privilege IAM, patching, automated EBS/DB backups, restore testing, CloudWatch alerts and secret management. A single VM is a **single point of failure**; document recovery and migrate when availability requirements justify it.

AWS cost comparisons must include EC2, EBS snapshots, public IPv4, RDS, load balancers, NAT gateways, CloudWatch and data transfer. Use AWS Pricing Calculator with the chosen region and load. This PR provisions **no AWS resources**.
