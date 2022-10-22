import json
import boto3
import requests
#from elasticsearch import Elasticsearch, RequestsHttpConnection
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

    
SUBJECT = "This is test email for testing purpose..!!"

# The email body for recipients with non-HTML email clients.
BODY_TEXT = ("Hey Hi...\r\n"
            "This email was sent with Amazon SES using the "
            "AWS SDK for Python (Boto)."
            )
            
         

def sendEmail(email, rest_details):
    BODY_HTML = """<html>
    <head></head>
    <body>
    <h1>Hello!</h1>
    <p>This email was sent with
        <a href=' '>Amazon SES CQPOCS</a > using the
        <a href='https://aws.amazon.com/sdk-for-python/'>
        AWS SDK for Python (Boto)</a >.</p >
        {}
    </body>
    </html>
                """.format(rest_details)   
    ses_client = boto3.client("ses", region_name="us-east-1")
    response = ses_client.send_email(
        Destination={
            'ToAddresses': [
                email,
            ],
        },
        Message={
            'Body': {
                'Html': {
                    'Data': BODY_HTML
                },
                'Text': {
                    'Data': BODY_TEXT
                },
            },
            'Subject': {
                'Data': SUBJECT
            },
        },
        Source='yuting.robotemailsend@gmail.com'
    )


def search(cuisine):
    payload = {
        "query": {
            "match":{
                "Cuisine" : str(cuisine)
            }
        }
    }
    url = 'https://search-restaurants-6wsdi6hjbx5bzkdhvsb3dp6rlm.us-east-1.es.amazonaws.com/' + 'restaurants/Restaurant/_search'
    data = requests.get(url, auth = ('user1', 'test'), json=payload).json()#.content.decode()
    #data = es.search(index="restaurants", body={"query": {"match": {'Cuisine':cuisine}}})
    print("search complete", data.get('hits').get('hits'))#['hits']['hits'])
    return data['hits']['hits']


def get_restaurant_data(ids):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('yelp_restaurants2')
    ans = 'Hi! Here are our recommendations,\n '
    i = 1
    
    for id in ids:
        if i<=3:
            response = table.get_item(
                Key={
                    'id': id
                }
            )
            print(response)
            response_item = response.get("Item")
            print(response_item)
            restaurant_name = response_item['name']
            restaurant_address = eval(response_item['Address'])['address1']
            #restaurant_phoneNumber = response_item['phone_number']
            restaurant_rating = response_item['rating']
            ans += "<p>{}. {}, with {} stars, located at {} </p>".format(i, restaurant_name, restaurant_rating, restaurant_address)
            # return ans
            i += 1
        else:
            break
    
    print(ans)
    return ans 


def lambda_handler(event, context):
    # TODO implement
    # ids = search('chinese')
    # rest_details = get_restaurant_data(ids)

    messages = event['Records'][0]['messageAttributes']
    print(messages)
    print('Hello1')
    try:
        # message = messages
        # message1 = json.loads(message)
        location = messages.get('Location').get('stringValue')
        cuisine = messages.get('Cuisine').get('stringValue')
        dining_time = messages.get('DiningTime').get('stringValue')
        num_people = messages.get('NumberOfPeople').get('stringValue')
        email = messages.get('Email').get('stringValue')
        print(location, cuisine, dining_time, num_people, email)
        # sendEmail(email, num_people)
        ids = search(cuisine)
        ids = list(map(lambda x: x['_source']['ID'], ids))
        print("check iDdidididididididiididididididiididid")
        print(ids)
        rest_details = get_restaurant_data(ids)
        sendEmail(email, rest_details)
    except Exception as e:
        print(e)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda LF2!')
    }
