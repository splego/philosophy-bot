def lambda_handler(event, context):
    print("batch start")

    # 仮データ
    users = ["test_user_id"]

    for user in users:
        print("send to:", user)

    return {
        "statusCode": 200,
        "body": "OK"
    }