import json
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("users")

def lambda_handler(event, context):
    response = table.scan()

    items = responce.get("Items", [])

    print("ITEMS:", items)

    return {
        "statusCode": 200,
        "body": json.dumps(items)
    }