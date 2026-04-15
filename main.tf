# AWS Cloud Migration Test Infrastructure
# Services: Lambda, DynamoDB, S3, Bedrock, CloudWatch

terraform {
  required_version = ">= 1.0"
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

# Variables
variable "aws_region" {
  default = "us-east-1"
}

variable "environment" {
  default = "dev"
}

# S3 Bucket for Agent Artifacts
resource "aws_s3_bucket" "agent_artifacts" {
  bucket = "cloud-migration-agent-artifacts-${data.aws_caller_identity.current.account_id}"

  tags = {
    Environment = var.environment
    Service     = "ai-agent"
  }
}

# DynamoDB Table for Agent State
resource "aws_dynamodb_table" "agent_state" {
  name           = "cloud-migration-agent-state"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "agent_id"
  range_key      = "timestamp"

  attribute {
    name = "agent_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  tags = {
    Environment = var.environment
    Service     = "ai-agent"
  }
}

# Lambda Execution Role
resource "aws_iam_role" "lambda_role" {
  name = "cloud-migration-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Lambda Policy for Bedrock, DynamoDB, S3
resource "aws_iam_role_policy" "lambda_policy" {
  name = "cloud-migration-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock-runtime:InvokeModel"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query"
        ]
        Resource = aws_dynamodb_table.agent_state.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.agent_artifacts.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Lambda Function for Agent Orchestration
resource "aws_lambda_function" "agent_orchestrator" {
  filename      = "lambda_handler.zip"
  function_name = "cloud-migration-agent-orchestrator"
  role          = aws_iam_role.lambda_role.arn
  handler       = "app.lambda_handler"
  runtime       = "python3.11"
  timeout       = 300
  memory_size   = 512

  environment {
    variables = {
      DYNAMODB_TABLE     = aws_dynamodb_table.agent_state.name
      S3_BUCKET          = aws_s3_bucket.agent_artifacts.bucket
      BEDROCK_REGION     = var.aws_region
      BEDROCK_MODEL_ID   = "anthropic.claude-3-sonnet-20240229-v1:0"
    }
  }

  tags = {
    Environment = var.environment
    Service     = "ai-agent"
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "agent_logs" {
  name              = "/aws/lambda/cloud-migration-agent"
  retention_in_days = 7

  tags = {
    Environment = var.environment
    Service     = "ai-agent"
  }
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# Outputs
output "dynamodb_table_name" {
  value = aws_dynamodb_table.agent_state.name
}

output "s3_bucket_name" {
  value = aws_s3_bucket.agent_artifacts.bucket
}

output "lambda_function_arn" {
  value = aws_lambda_function.agent_orchestrator.arn
}
