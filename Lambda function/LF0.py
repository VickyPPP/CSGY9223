import json
import boto3
from json import dumps
        
def lambda_handler(event, context):
    client = boto3.client('lex-runtime')
    # userId = context.aws_request_id
    response = client.post_text(
        botName = 'OrderFlowers',
        botAlias = 'yuting',
        userId = '01',
        sessionAttributes = {},
        requestAttributes = {},
        inputText=event['messages'][0]['unstructured']['text']
    )
    return {
        "statusCode": 200,
        "messages": [
          {
            "type": "unstructured",
            "unstructured": {
              "id": "string",
              "text": json.dumps(response['message'])[1:-1],
              "timestamp": "string"
            }
          }
        ],
    }
    