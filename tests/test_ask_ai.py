import json
import boto3
import pytest
from datetime import datetime, timedelta

# Mock the required utilities and dependencies
class MockDBUtils:
    @staticmethod
    def extract_id(event, key):
        return event.get('queryStringParameters', {}).get(key)

    @staticmethod
    def execute_statement(statement):
        # Mock database response
        return [{
            'prediction_id': 'pred123',
            'ser_id': 'ser123',
            'timestamp': '2025-03-24T13:10:23'
        }]

    @staticmethod
    def prepare_get_response(service_name, response):
        return {
            'status': 'success',
            'data': response,
            'errors': []
        }

class MockReqUtils:
    @staticmethod
    def is_super_user(event):
        return event.get('is_super_user', False)

# Test cases for askAI Lambda function
def test_ask_ai_with_service_id():
    event = {
        'queryStringParameters': {
            'serviceId': 'ser123'
        }
    }
    
    response = process_get_request(event)
    assert response['status'] == 'success'
    assert len(response['data']) > 0
    assert response['data'][0]['ser_id'] == 'ser123'

def test_ask_ai_with_prediction_id():
    event = {
        'queryStringParameters': {
            'predictionId': 'pred123'
        }
    }
    
    response = process_get_request(event)
    assert response['status'] == 'success'
    assert len(response['data']) > 0
    assert response['data'][0]['prediction_id'] == 'pred123'

def test_ask_ai_with_timestamps():
    event = {
        'queryStringParameters': {
            'serviceId': 'ser123',
            'startTimestamp': '2025-03-24T12:00:00',
            'endTimestamp': '2025-03-24T14:00:00'
        }
    }
    
    response = process_get_request(event)
    assert response['status'] == 'success'
    assert len(response['data']) > 0

def test_ask_ai_monitor_mode():
    event = {
        'queryStringParameters': {
            'mode': 'monitor'
        },
        'is_super_user': True
    }
    
    response = process_get_request(event)
    assert response['status'] == 'success'

def test_ask_ai_missing_required_params():
    event = {
        'queryStringParameters': {}
    }
    
    response = process_get_request(event)
    assert response == 'please provide serviceId or predictionId'

# Mock the required dependencies
dbutils = MockDBUtils()
req_utils = MockReqUtils()
TABLE_NAME = "ask_ai_table"

# Import the function to test
def process_get_request(event):
    ser_id = dbutils.extract_id(event, 'serviceId')
    prediction_id = dbutils.extract_id(event, 'predictionId')
    mode = dbutils.extract_id(event, 'mode')
    start_timestamp = dbutils.extract_id(event, 'startTimestamp')
    end_timestamp = dbutils.extract_id(event, 'endTimestamp')

    if not ser_id and not prediction_id and not (mode == 'monitor' and req_utils.is_super_user(event)):
        return 'please provide serviceId or predictionId'

    statement = "select * from "+TABLE_NAME
    queries = []

    if ser_id:
        queries.append(' ser_id="'+ser_id+'"')
    elif prediction_id:
        queries.append(' prediction_id="'+prediction_id+'"')
    if start_timestamp:
        queries.append(' timestamp > "'+start_timestamp+'"')
    if end_timestamp:
        queries.append(' timestamp <= "'+end_timestamp+'"')

    for index, query in enumerate(queries):
        if index == 0:
            statement += " where" + query
        else:
            statement += " and" + query

    if not len(queries):
        order_stmt = " order by timestamp desc limit 100"
        statement += order_stmt

    stmt_response = dbutils.execute_statement(statement)
    response = dbutils.prepare_get_response('askAI', stmt_response)
    return response
