"""
This sample demonstrates an implementation of the Lex Code Hook Interface
in order to serve a sample bot which manages orders for flowers.
Bot, Intent, and Slot models which are compatible with this sample can be found in the Lex Console
as part of the 'OrderFlowers' template.

For instructions on how to set up and test this bot, as well as additional samples,
visit the Lex Getting Started documentation http://docs.aws.amazon.com/lex/latest/dg/getting-started.html.
"""
import math
import boto3
import dateutil.parser
import datetime
import time
import os
import logging
import random
# import re
# EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """


def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


""" --- Helper Functions --- """


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')


def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False


def validate_dining_info(slots):
    cities = ['new york']
    if slots['Location'] is not None and slots['Location'].lower() not in cities:
        return build_validation_result(False,
                                      'Location',
                                      'Please enter valid location'
                                      )
    Cuisine_type = ['tradamerica', 'japanese', 'chinese','italian',' mexican']
    if slots['Cuisine'] is not None and slots['Cuisine'].lower() not in Cuisine_type:
        return build_validation_result(False,
                                       'Cuisine',
                                       'We do not have {}, would you like a different type of cuisine?  '
                                       'Our most popular cuisine are roses'.format(slots['Cuisine']))
    if slots['NumberOfPeople'] is not None and int(slots['NumberOfPeople']) <= 0:
        return build_validation_result(False,
                                       'NumberOfPeople',
                                       'Please enter valid NumberOfPeople'
                                       )
    # if date is not None:
    #     if not isvalid_date(date):
    #         return build_validation_result(False, 'PickupDate', 'I did not understand that, what date would you like to pick the flowers up?')
    #     elif datetime.datetime.strptime(date, '%Y-%m-%d').date() <= datetime.date.today():
    #         return build_validation_result(False, 'PickupDate', 'You can pick up the flowers from tomorrow onwards.  What day would you like to pick them up?')
    if slots['Email'] is not None:
        ses_client = boto3.client("ses", region_name="us-east-1")
        email_list = ses_client.list_verified_email_addresses()['VerifiedEmailAddresses']
        if slots['Email'] not in email_list:
            response = ses_client.verify_email_identity(EmailAddress = slots['Email'])
            return build_validation_result(False,
                                          'Email',
                                          'Please valid your email address and input the email address again'
                                          )
    if slots['DiningTime'] is not None:
        if len(slots['DiningTime']) != 5:
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'DiningTime', None)

        hour, minute = slots['DiningTime'].split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'DiningTime', None)

        if hour < 10 or hour > 16:
            # Outside of business hours
            return build_validation_result(False, 'DiningTime', 'Our business hours are from ten a m. to five p m. Can you specify a time during this range?')

    return build_validation_result(True, None, None)


""" --- Functions that control the bot's behavior --- """


def book_dining_info(intent_request):
    """
    Performs dialog management and fulfillment for ordering flowers.
    Beyond fulfillment, the implementation of this intent demonstrates the use of the elicitSlot dialog action
    in slot validation and re-prompting.
    """
    Location = get_slots(intent_request)["Location"]
    Cuisine = get_slots(intent_request)["Cuisine"]
    DiningTime = get_slots(intent_request)["DiningTime"]
    NumberOfPeople = get_slots(intent_request)['NumberOfPeople']
    Email = get_slots(intent_request)['Email']
    source = intent_request['invocationSource']

    if source == 'DialogCodeHook':
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt for the first violation detected.
        slots = get_slots(intent_request)

        validation_result = validate_dining_info(slots)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                              intent_request['currentIntent']['name'],
                              slots,
                              validation_result['violatedSlot'],
                              validation_result['message'])

        # Pass the price of the flowers back through session attributes to be used in various prompts defined
        # on the bot model.
        
        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
        # if flower_type is not None:
        #     output_session_attributes['Price'] = len(flower_type) * 5  # Elegant pricing model
        return delegate(output_session_attributes, get_slots(intent_request))

    elif source == 'FulfillmentCodeHook':
        sqs_client = boto3.client("sqs", region_name="us-east-1")
        # queue = sqs_client.get_queue_by_name(QueueName='Queue1.fifo')
        # diningTime = "breakfast"
        # if (DiningTime )
        queue_url = sqs_client.get_queue_url(QueueName='Queue1.fifo')['QueueUrl']
        response = sqs_client.send_message(
            QueueUrl = queue_url,
            MessageAttributes={
                "Location": {
                      'DataType' : 'String',
                      'StringValue' : Location
                  },
                  "Cuisine": {
                      'DataType' : 'String',
                      'StringValue' : Cuisine
                  },
                  "DiningTime": {
                      'DataType' : 'String',
                      'StringValue' : DiningTime
                  },
                  "NumberOfPeople": {
                      'DataType' : 'Number',
                      'StringValue' : NumberOfPeople
                  },
                  "Email": {
                      'DataType' : 'String',
                      'StringValue' : Email
                  }
            },
            MessageBody='string',
            MessageDeduplicationId='string',
            MessageGroupId='string'
        )
        

    # Order the flowers, and rely on the goodbye message of the bot to define the message to the end user.
    # In a real bot, this would likely involve a call to a backend service.
        return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Thanks, your order for {} has been placed and will be ready at {} for {} people'.format(Email, DiningTime, NumberOfPeople)})


""" --- Intents --- """
def thankyou(intent_request):
    output = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    return close(
        output,
        'Fulfilled',
        {
            'contentType' : 'PlainText',
            'content' : "You are welcome."
        }
    )

def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'DiningSuggestionsIntent':
        return book_dining_info(intent_request)
    elif intent_name == 'ThankYouIntent':
        return thankyou(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
