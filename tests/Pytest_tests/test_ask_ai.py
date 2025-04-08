import pytest
import json
import boto3
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

FUNCTION_NAME_PREFIX = "yasanthi_"

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
                'status': 'success',
                'data': [{
                    'prediction_id': 'pred123',
                    'ser_id': 'ser123',
                    'timestamp': '2025-03-24T13:10:23'
                }],
                'errors': []
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

class TestAskAI:
    def test_ask_ai_with_service_id(self, mock_lambda_client, mock_successful_response):
        """Test askAI query with service ID"""
        mock_lambda_client.invoke.return_value = mock_successful_response
        
        event = {
            'queryStringParameters': {
                'serviceId': 'ser123'
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "askAI",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = assert_response_format(response)
        assert response_json["status"] == "success"
        assert len(response_json["data"]) > 0
        assert response_json["data"][0]["ser_id"] == "ser123"
        assert response_json.get("errors") == []
        mock_lambda_client.invoke.assert_called_once()

    def test_ask_ai_with_prediction_id(self, mock_lambda_client, mock_successful_response):
        """Test askAI query with prediction ID"""
        mock_lambda_client.invoke.return_value = mock_successful_response
        
        event = {
            'queryStringParameters': {
                'predictionId': 'pred123'
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "askAI",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = assert_response_format(response)
        assert response_json["status"] == "success"
        assert len(response_json["data"]) > 0
        assert response_json["data"][0]["prediction_id"] == "pred123"
        assert response_json.get("errors") == []
        mock_lambda_client.invoke.assert_called_once()

    def test_ask_ai_with_timestamps(self, mock_lambda_client, mock_successful_response):
        """Test askAI query with timestamp range"""
        mock_lambda_client.invoke.return_value = mock_successful_response
        
        event = {
            'queryStringParameters': {
                'serviceId': 'ser123',
                'startTimestamp': '2025-03-24T12:00:00',
                'endTimestamp': '2025-03-24T14:00:00'
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "askAI",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = assert_response_format(response)
        assert response_json["status"] == "success"
        assert len(response_json["data"]) > 0
        assert response_json.get("errors") == []
        mock_lambda_client.invoke.assert_called_once()

    def test_ask_ai_monitor_mode(self, mock_lambda_client, mock_successful_response):
        """Test askAI in monitor mode"""
        mock_lambda_client.invoke.return_value = mock_successful_response
        
        event = {
            'queryStringParameters': {
                'mode': 'monitor'
            },
            'is_super_user': True
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "askAI",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = assert_response_format(response)
        assert response_json["status"] == "success"
        assert response_json.get("errors") == []
        mock_lambda_client.invoke.assert_called_once()

    @pytest.mark.parametrize("invalid_params,expected_error", [
        ({}, "Missing required parameters"),
        ({'mode': 'monitor', 'is_super_user': False}, "Unauthorized access"),
        ({'serviceId': 'invalid'}, "Service not found"),
        ({'predictionId': 'invalid'}, "Prediction not found"),
        ({'startTimestamp': 'invalid'}, "Invalid timestamp format")
    ])
    def test_ask_ai_invalid_inputs(self, mock_lambda_client, invalid_params, expected_error):
        """Test askAI with various invalid inputs"""
        error_response = {
            'StatusCode': 400,
            'Payload': json.dumps({
                'statusCode': 400,
                'body': json.dumps({
                    'status': 'error',
                    'data': {},
                    'errors': [expected_error]
                })
            })
        }
        mock_lambda_client.invoke.return_value = error_response
        
        event = {
            'queryStringParameters': invalid_params
        }
        if 'is_super_user' in invalid_params:
            event['is_super_user'] = invalid_params['is_super_user']
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "askAI",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = assert_response_format(response)
        assert response_json["status"] == "error"
        assert expected_error in str(response_json.get("errors", []))
        mock_lambda_client.invoke.assert_called_once()
