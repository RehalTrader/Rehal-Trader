# AWS Deployment Guide

Two supported paths, from simplest to most scalable. Pick one — don't mix them.

## Option A — Single EC2 instance + Docker Compose (fastest to ship)

Good for MVP / low-to-moderate traffic. This is what `.github/workflows/ci-cd.yml`'s
`deploy` job targets by default.

1. Launch an EC2 instance (Ubuntu 24.04, t3.medium or larger, at least 20GB disk).
2. Open security group ports: 22 (SSH, restrict to your IP), 80, 443.
3. Install Docker + Compose plugin:
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   sudo apt-get install -y docker-compose-plugin
   ```
4. Point a domain's A record at the instance's Elastic IP.
5. Get a TLS cert (Let's Encrypt via certbot, or upload your own) into `nginx/certs/`.
6. Clone the repo to `/opt/trading-signal-platform`, copy `.env.example` to `.env` and
   fill in real secrets (never commit `.env`).
7. `docker compose up -d --build`.
8. Add the following GitHub Actions repo secrets so CI/CD can auto-deploy on push to `main`:
   `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`.
9. Run migrations + seed once: `docker compose exec backend alembic upgrade head`
   then `docker compose exec backend python -m app.db.seed`.

Attach an RDS Postgres and ElastiCache Redis instance instead of the bundled containers
once traffic grows — just point `DATABASE_URL` / `REDIS_URL` at them and remove the
`postgres` / `redis` services from `docker-compose.yml`.

## Option B — ECS Fargate (managed, auto-scaling)

Use the task definitions in `deploy/aws/ecs-task-definitions/`. High-level steps:

1. Push images to ECR (or keep using GHCR — ECS can pull from either with the right
   repository credentials configured).
2. Create an RDS Postgres (Multi-AZ for production) and an ElastiCache Redis cluster.
3. Create an ECS cluster (Fargate launch type).
4. Register the task definitions (`backend-task-def.json`, `frontend-task-def.json`),
   substituting your ECR image URIs, RDS/Redis endpoints, and secrets ARNs
   (store `JWT_SECRET_KEY`, `STRIPE_SECRET_KEY`, etc. in AWS Secrets Manager —
   never as plain task-definition environment variables).
5. Create an Application Load Balancer with two target groups (backend:8000, frontend:3000)
   and path-based routing (`/api/*`, `/ws/*` -> backend; everything else -> frontend).
6. Create ECS services referencing each task definition, attached to the ALB target groups.
7. Point Route 53 at the ALB; request an ACM certificate for HTTPS termination on the ALB
   (this replaces nginx's TLS role — you can drop the `nginx` container entirely on this path).
8. Update the CI/CD `deploy` job to call `aws ecs update-service --force-new-deployment`
   instead of SSHing into a host.

### Security checklist for either path
- Rotate `JWT_SECRET_KEY` and all API keys before going live; never reuse the example values.
- Put RDS/ElastiCache in private subnets; only the app tier's security group may reach them.
- Enable RDS automated backups and set a real backup retention window.
- Turn on AWS WAF (or Cloudflare) in front of the ALB/EC2 for basic bot/DDoS filtering.
- Restrict CORS (`FRONTEND_URL` / `allow_origins`) to your real domain in production.
- Enable CloudWatch (or your log stack) to ingest the JSON-ish structured logs the
  backend already emits via `app/core/logging.py`.
