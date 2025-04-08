import pytest
import boto3
import json
from unittest.mock import MagicMock, patch
import lambda_utils as lutils

FUNCTION_NAME_PREFIX = "yasanthi_"

@pytest.fixture
def mock_lambda_client():
    with patch('lambda_utils.LAMBDA') as mock_lambda:
        yield mock_lambda

@pytest.fixture
def valid_student_payload():
    return {
        "body": json.dumps({
            "personId": "12345",
            "type": "student",
            "gradYear": 2025,
            "county": "Clark",
            "state": "NV",
            "interests": "Science, Math",
            "mentor": "Mentor Name",
            "schoolId": "school123"
        })
    }

@pytest.fixture
def minimal_student_payload():
    return {
        "body": json.dumps({
            "personId": "67890",
            "type": "student"
        })
    }

@pytest.fixture
def mock_successful_response():
    return {
        'StatusCode': 200,
        'Payload': json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'data': {'studentId': 'test123'},
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

    # Extract "body" if it exists and is a string
    if isinstance(response_json, dict) and "Payload" in response_json:
        try:
            payload = json.loads(response_json["Payload"])
            if "body" in payload:
                response_json = json.loads(payload["body"])
        except json.JSONDecodeError:
            pytest.fail("Response body is not valid JSON")
            return None
    
    return response_json

class TestDashboardStudent:
    def test_valid_input(self, mock_lambda_client, valid_student_payload, mock_successful_response):
        """Test dashboard student creation with valid full input"""
        mock_lambda_client.invoke.return_value = mock_successful_response
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "dashboardStudent",
            InvocationType="RequestResponse",
            Payload=json.dumps({
                "body": valid_student_payload["body"],
                "queryStringParameters": "",
                "httpMethod": "POST"
            })
        )
        
        response_json = assert_response_format(response)
        assert response_json["status"] == "success"
        assert "studentId" in response_json.get("data", {})
        assert response_json.get("errors") == []

        mock_lambda_client.invoke.assert_called_once()

    def test_minimal_input(self, mock_lambda_client, minimal_student_payload, mock_successful_response):
        """Test dashboard student creation with minimal input"""
        mock_lambda_client.invoke.return_value = mock_successful_response
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "dashboardStudent",
            InvocationType="RequestResponse",
            Payload=json.dumps({
                "body": minimal_student_payload["body"],
                "queryStringParameters": "",
                "httpMethod": "POST"
            })
        )
        
        response_json = assert_response_format(response)
        assert response_json["status"] == "success"
        assert "studentId" in response_json.get("data", {})
        assert response_json.get("errors") == []

        mock_lambda_client.invoke.assert_called_once()

    @pytest.mark.parametrize("invalid_payload,expected_error", [
        ({"body": json.dumps({"type": "student"})}, "Missing personId"),
        ({"body": json.dumps({"personId": "12345"})}, "Missing type"),
        ({"body": "invalid_json"}, "Invalid JSON"),
        ({}, "Empty payload")
    ])
    def test_invalid_inputs(self, mock_lambda_client, invalid_payload, expected_error):
        """Test dashboard student creation with various invalid inputs"""
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
            FunctionName=FUNCTION_NAME_PREFIX + "dashboardStudent",
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
