def lambda_handler(event, context):
    print("event:", event)

    user_id = event["events"][0]["source"]["userId"]

    # DB保存（あとで実装）
    print("user_id:", user_id)

    return {
        "statusCode": 200,
        "body": "OK"
    }