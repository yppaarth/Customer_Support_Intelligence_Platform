# Deployment Notes

Local development does not require AWS credentials. To deploy, review the Terraform in `infrastructure/aws`, add networking, ECS service definitions, RDS PostgreSQL with pgvector enabled, ElastiCache Redis, IAM roles, Secrets Manager values, and CloudWatch alarms, then run Terraform explicitly.

Do not store real secrets in `.env` or source control. Use AWS Secrets Manager or SSM Parameter Store and inject values at task runtime.

Backups should cover RDS automated snapshots, S3 document versioning, and Redis persistence only if cache data becomes operationally necessary.
