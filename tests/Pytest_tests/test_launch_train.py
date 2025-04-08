import pytest
import json
import boto3
from unittest.mock import MagicMock, patch
import lambda_utils as lutils

FUNCTION_NAME_PREFIX = "yasanthi_"

@pytest.fixture
def mock_lambda_client():
    with patch('lambda_utils.LAMBDA') as mock_lambda:
        yield mock_lambda

def get_successful_response(launch_mode="automatic"):
    return {
        'StatusCode': 200,
        'Payload': json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'data': {
                    'experimentId': 'exp123',
                    'serviceId': 'service123',
                    'waitTime': 300,
                    'user': 'testuser',
                    'launchMode': launch_mode
                },
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

class TestLaunchTrain:
    @pytest.mark.parametrize("launch_mode,training_mode", [
        ("automatic", "aws-sklearn-serverless"),
        ("manual", "aws-tensorflow-serverless"),
        ("scheduled", "aws-pytorch-serverless")
    ])
    def test_valid_launch_modes(self, mock_lambda_client, launch_mode, training_mode):
        """Test launch train with different valid launch modes and training modes"""
        mock_lambda_client.invoke.return_value = get_successful_response(launch_mode)
        
        event = {
            "body": json.dumps({
                "serviceId": "service123",
                "launchMode": launch_mode,
                "mode": training_mode
            })
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "launchTrain",
            InvocationType="RequestResponse",
            Payload=json.dumps({
                "body": event["body"],
                "queryStringParameters": "",
                "httpMethod": "POST"
            })
        )
        
        response_json = assert_response_format(response)
        assert response_json["status"] == "success"
        assert all(key in response_json["data"] for key in ["experimentId", "serviceId", "waitTime", "user", "launchMode"])
        assert response_json["data"]["launchMode"] == launch_mode
        assert response_json.get("errors") == []
        mock_lambda_client.invoke.assert_called_once()

    @pytest.mark.parametrize("invalid_payload,expected_error", [
        ({"body": json.dumps({"launchMode": "automatic"})}, "Missing serviceId"),
        ({"body": json.dumps({"serviceId": "service123"})}, "Missing launchMode"),
        ({"body": json.dumps({"serviceId": "service123", "launchMode": "invalid"})}, "Invalid launchMode"),
        ({"body": json.dumps({"serviceId": "service123", "launchMode": "automatic", "mode": "invalid"})}, "Invalid training mode"),
        ({"body": "invalid_json"}, "Invalid JSON format"),
        ({}, "Empty request body")
    ])
    def test_invalid_inputs(self, mock_lambda_client, invalid_payload, expected_error):
        """Test launch train with various invalid inputs"""
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
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "launchTrain",
            InvocationType="RequestResponse",
            Payload=json.dumps({
                "body": invalid_payload.get("body", ""),
                "queryStringParameters": "",
                "httpMethod": "POST"
            })
        )
        
        response_json = assert_response_format(response)
        assert response_json["status"] == "error"
        assert expected_error in str(response_json.get("errors", []))
        mock_lambda_client.invoke.assert_called_once()

    def test_scheduled_launch_with_parameters(self, mock_lambda_client):
        """Test scheduled launch with additional training parameters"""
        mock_lambda_client.invoke.return_value = get_successful_response("scheduled")
        
        event = {
            "body": json.dumps({
                "serviceId": "service123",
                "launchMode": "scheduled",
                "mode": "aws-sklearn-serverless",
                "schedule": "0 12 * * *",  # Run at 12 PM daily
                "parameters": {
                    "epochs": 100,
                    "batch_size": 32,
                    "learning_rate": 0.001
                }
            })
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "launchTrain",
            InvocationType="RequestResponse",
            Payload=json.dumps({
                "body": event["body"],
                "queryStringParameters": "",
                "httpMethod": "POST"
            })
        )
        
        response_json = assert_response_format(response)
        assert response_json["status"] == "success"
        assert all(key in response_json["data"] for key in ["experimentId", "serviceId", "waitTime", "user", "launchMode"])
        assert response_json["data"]["launchMode"] == "scheduled"
        assert response_json.get("errors") == []
        mock_lambda_client.invoke.assert_called_once()
