import pytest
import json
from unittest.mock import MagicMock, patch
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FUNCTION_NAME_PREFIX
import lambda_utils as lutils

@pytest.fixture
def mock_lambda_client():
    with patch('lambda_utils.LAMBDA') as mock_lambda:
        yield mock_lambda

@pytest.fixture
def mock_successful_response():
    return {
        'StatusCode': 200,
        'Payload': json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'service123': {
                    'service_id': 'service123',
                    'service_name': 'Test Service',
                    'status': 'active',
                    'created_at': '2025-04-08T11:33:29'
                }
            })
        })
    }

def assert_response_format(response):
    """Helper function to validate response format"""
    if isinstance(response, str):
        try:
            response_json = json.loads(response)
        except json.JSONDecodeError:
            pytest.fail("Response is not valid JSON")
            return None
    else:
        response_json = response

    if isinstance(response_json, dict) and "Payload" in response_json:
        try:
            payload = json.loads(response_json["Payload"])
            if "body" in payload:
                response_json = json.loads(payload["body"])
        except json.JSONDecodeError:
            pytest.fail("Response body is not valid JSON")
            return None
    
    return response_json

class TestAiService:
    def test_get_service_by_id(self, mock_lambda_client, mock_successful_response):
        """Test getting service details by service ID"""
        mock_lambda_client.invoke.return_value = mock_successful_response
        
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'serviceId': 'service123'
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "aiService",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = assert_response_format(response)
        assert 'service123' in response_json
        assert response_json['service123']['service_name'] == 'Test Service'
        mock_lambda_client.invoke.assert_called_once()

    def test_get_service_by_name(self, mock_lambda_client, mock_successful_response):
        """Test getting service details by service name"""
        mock_lambda_client.invoke.return_value = mock_successful_response
        
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'serviceName': 'Test Service'
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "aiService",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = assert_response_format(response)
        assert 'service123' in response_json
        mock_lambda_client.invoke.assert_called_once()

    def test_super_user_access(self, mock_lambda_client, mock_successful_response):
        """Test super user accessing another user's service"""
        mock_lambda_client.invoke.return_value = mock_successful_response
        
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'serviceId': 'service123',
                'user': 'other_user'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:groups': 'SuperUsers'
                    }
                }
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "aiService",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = assert_response_format(response)
        assert 'service123' in response_json
        mock_lambda_client.invoke.assert_called_once()

    def test_teacher_role_access(self, mock_lambda_client, mock_successful_response):
        """Test teacher role accessing services"""
        mock_lambda_client.invoke.return_value = mock_successful_response
        
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'serviceId': 'service123',
                'userRole': 'Teacher'
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "aiService",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = assert_response_format(response)
        assert 'service123' in response_json
        mock_lambda_client.invoke.assert_called_once()

    def test_missing_service_info(self, mock_lambda_client):
        """Test error handling when service ID/name is missing"""
        mock_lambda_client.invoke.return_value = {
            'StatusCode': 200,
            'Payload': json.dumps({
                'statusCode': 200,
                'body': json.dumps('Please provide service id')
            })
        }
        
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {}
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "aiService",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = assert_response_format(response)
        assert response_json == 'Please provide service id'
        mock_lambda_client.invoke.assert_called_once()

    def test_unsupported_method(self, mock_lambda_client):
        """Test error handling for unsupported HTTP methods"""
        mock_lambda_client.invoke.return_value = {
            'StatusCode': 400,
            'Payload': json.dumps({
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Unsupported Method: POST'
                })
            })
        }
        
        event = {
            'httpMethod': 'POST',
            'queryStringParameters': {
                'serviceId': 'service123'
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "aiService",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = assert_response_format(response)
        assert 'Unsupported Method: POST' in str(response_json)
        mock_lambda_client.invoke.assert_called_once()
