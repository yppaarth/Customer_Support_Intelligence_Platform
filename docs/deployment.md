# Deployment Notes

Local development does not require AWS credentials. This repository is prepared for an AWS deployment path, but it does not claim that a live AWS environment exists.

To deploy, review the Terraform in `infrastructure/aws`, add networking, ECS service definitions, RDS PostgreSQL with pgvector enabled, ElastiCache Redis, IAM roles, Secrets Manager values, and CloudWatch alarms, then run Terraform explicitly.

Do not store real secrets in `.env` or source control. Use AWS Secrets Manager or SSM Parameter Store and inject values at task runtime.

Backups should cover RDS automated snapshots, S3 document versioning, and Redis persistence only if cache data becomes operationally necessary.

## Suggested AWS Runbook

1. Create a non-production AWS account or isolated environment.
2. Store application secrets in AWS Secrets Manager or SSM Parameter Store.
3. Build and push API, worker, and frontend images to ECR.
4. Provision VPC, private subnets, security groups, RDS PostgreSQL with pgvector, ElastiCache Redis, and S3.
5. Run Alembic migrations against RDS.
6. Start ECS Fargate services.
7. Configure CloudWatch log groups, alarms, and dashboards.
8. Seed fictional demo data only in non-production environments.
9. Run smoke tests for `/api/v1/health`, login, document ingestion, ticket creation, cited draft generation, and approval.

## Honest Status

- Docker and AWS infrastructure scaffolding exist.
- Local migrations and tests have been verified.
- A live AWS deployment has not been verified from this repository.
