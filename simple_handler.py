"""
app.py — Lambda handler using AWS services (S3, DynamoDB, CloudWatch).
This file is analyzed by the cloud migrator to detect AI stack and cloud services.
"""
import os
import json
import boto3
import logging

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

# AWS service clients — detected by cloud migrator
s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

S3_BUCKET = os.getenv("S3_BUCKET", "my-app-data-bucket-prod")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "users-table")


def main(event, context):
    """Main Lambda handler."""
    action = event.get("action", "get")
    user_id = event.get("userId", "")

    table = dynamodb.Table(DYNAMODB_TABLE)

    if action == "get":
        response = table.get_item(Key={"userId": user_id, "createdAt": event.get("createdAt", "")})
        return {"statusCode": 200, "body": json.dumps(response.get("Item", {}))}

    elif action == "save":
        data = event.get("data", {})
        # Save to DynamoDB
        table.put_item(Item={"userId": user_id, "createdAt": event.get("createdAt"), **data})
        # Archive to S3
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=f"users/{user_id}/archive.json",
            Body=json.dumps(data),
        )
        return {"statusCode": 200, "body": json.dumps({"saved": True})}

    elif action == "list":
        response = table.query(
            KeyConditionExpression="userId = :uid",
            ExpressionAttributeValues={":uid": user_id},
        )
        return {"statusCode": 200, "body": json.dumps(response.get("Items", []))}

    return {"statusCode": 400, "body": json.dumps({"error": "Unknown action"})}
