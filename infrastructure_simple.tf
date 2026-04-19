terraform {
  required_version = ">= 1.3.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# ─────────────────────────────────────────────────────────────────────────────
# IAM Role — Lambda execution role
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_iam_role" "lambda_exec_role" {
  name = "lambda-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# ─────────────────────────────────────────────────────────────────────────────
# IAM Role Policy — permissions for Lambda to access S3, DynamoDB, CloudWatch
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_iam_role_policy" "lambda_policy" {
  name = "lambda-s3-dynamodb-policy"
  role = aws_iam_role.lambda_exec_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
        Resource = [
          "${aws_s3_bucket.app_data.arn}",
          "${aws_s3_bucket.app_data.arn}/*"
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem", "dynamodb:Query", "dynamodb:Scan"]
        Resource = aws_dynamodb_table.users.arn
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "${aws_cloudwatch_log_group.lambda_logs.arn}:*"
      }
    ]
  })

  depends_on = [aws_iam_role.lambda_exec_role]
}

# ─────────────────────────────────────────────────────────────────────────────
# S3 Bucket — application data storage
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_s3_bucket" "app_data" {
  bucket = "my-app-data-bucket-prod"

  tags = {
    Name        = "app-data"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}

resource "aws_s3_bucket_versioning" "app_data_versioning" {
  bucket = aws_s3_bucket.app_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# DynamoDB Table — user records
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_dynamodb_table" "users" {
  name           = "users-table"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "userId"
  range_key      = "createdAt"

  attribute {
    name = "userId"
    type = "S"
  }

  attribute {
    name = "createdAt"
    type = "S"
  }

  global_secondary_index {
    name            = "CreatedAtIndex"
    hash_key        = "createdAt"
    projection_type = "ALL"
  }

  tags = {
    Name        = "users-table"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# CloudWatch Log Group — Lambda function logs
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/my-app-function"
  retention_in_days = 30

  tags = {
    Name        = "lambda-logs"
    Environment = "production"
  }
}

# CloudWatch Metric Alarm — Lambda errors alerting
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "lambda-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Alert when Lambda errors exceed threshold"

  dimensions = {
    FunctionName = aws_lambda_function.app_handler.function_name
  }

  depends_on = [aws_lambda_function.app_handler]
}

# ─────────────────────────────────────────────────────────────────────────────
# Lambda Function — main application handler
# Dependencies: IAM role, S3 bucket, DynamoDB table, CloudWatch log group
# ─────────────────────────────────────────────────────────────────────────────
resource "aws_lambda_function" "app_handler" {
  function_name = "my-app-function"
  role          = aws_iam_role.lambda_exec_role.arn
  handler       = "handler.main"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 256

  filename         = "function.zip"
  source_code_hash = filebase64sha256("function.zip")

  environment {
    variables = {
      S3_BUCKET      = aws_s3_bucket.app_data.bucket
      DYNAMODB_TABLE = aws_dynamodb_table.users.name
      LOG_LEVEL      = "INFO"
    }
  }

  logging_config {
    log_format = "JSON"
    log_group  = aws_cloudwatch_log_group.lambda_logs.name
  }

  depends_on = [
    aws_iam_role_policy.lambda_policy,
    aws_cloudwatch_log_group.lambda_logs,
  ]

  tags = {
    Name        = "app-handler"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}
