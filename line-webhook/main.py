import json
import boto3
import uuid

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("users")

def lambda_handler(event, context):
    print("EVENT:", json.dumps(event))

    # とりあえずダミーデータ
    user_id = str(uuid.uuid4())

    # DB保存（あとで実装）
    table.put_item(
        Item = {
            "userId": user_id,
            "test": "GOOD!"
        }
    )
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "written"})
    }