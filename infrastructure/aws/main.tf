terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_s3_bucket" "documents" {
  bucket_prefix = "resolveiq-documents-"
}

resource "aws_cloudwatch_log_group" "app" {
  name              = "/resolveiq/app"
  retention_in_days = 30
}

# ECS Fargate, RDS PostgreSQL with pgvector, and ElastiCache Redis are intentionally
# represented as scaffolding variables/modules so operators review cost and networking
# choices before provisioning paid resources.
