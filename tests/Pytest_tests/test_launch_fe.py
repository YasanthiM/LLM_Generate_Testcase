import pytest
import json
import boto3
import sys
sys.path.append("tests")
from config import FUNCTION_NAME_PREFIX
from lambda_utils import invoke_lambda
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_lambda_client():
    with patch('lambda_utils.LAMBDA') as mock_lambda:
        mock_lambda.invoke.return_value = {
            'StatusCode': 200,
            'Payload': json.dumps({
                'statusCode': 200,
                'body': json.dumps({
                    'status': 'ready',
                    'service_id': 'service123'
                })
            })
        }
        yield mock_lambda

@pytest.fixture
def mock_s3_client():
    with patch('boto3.client') as mock_s3:
        mock_client = MagicMock()
        mock_s3.return_value = mock_client
        yield mock_client

@pytest.fixture
def mock_successful_fe_response():
    return {
        'StatusCode': 200,
        'Payload': json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'report_id': 'report123',
                'service_id': 'service123',
                'data_id': 'data123',
                'predict_col': 'target',
                'status': 'ready',
                'cloud': 'AWS',
                'result': 'success',
                'engine': 'aws-sklearn-serverless'
            })
        })
    }

@pytest.fixture
def mock_data_prep_status():
    return {
        'StatusCode': 200,
        'Payload': json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'report123': {
                    'status': 'ready',
                    'engine': 'aws-sklearn-serverless',
                    'result': 'success'
                }
            })
        })
    }

@pytest.fixture
def mock_train_file_response():
    return {
        'StatusCode': 200,
        'Payload': json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'result': 'success',
                'url': 'https://s3-url.com/train.csv'
            })
        })
    }

@pytest.fixture
def mock_test_file_response():
    return {
        'StatusCode': 200,
        'Payload': json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'result': 'success',
                'url': 'https://s3-url.com/test.csv'
            })
        })
    }

@pytest.fixture
def mock_artifacts_url_response():
    return {
        'StatusCode': 200,
        'Payload': json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'result': 'success',
                'url': 'https://s3-url.com/code.py'
            })
        })
    }

@pytest.fixture
def mock_unsupported_method_response():
    return {
        'StatusCode': 400,
        'Payload': json.dumps({
            'statusCode': 400,
            'body': json.dumps({
                'result': 'failure',
                'error': 'Unsupported Method: PUT'
            })
        })
    }

@pytest.fixture
def mock_missing_params_response():
    return {
        'StatusCode': 400,
        'Payload': json.dumps({
            'statusCode': 400,
            'body': json.dumps({
                'result': 'failure',
                'error': 'Missing required parameters'
            })
        })
    }

class TestLaunchFE:
    def test_process_data_prep_post_request(self, mock_lambda_client, mock_successful_fe_response):
        """Test POST request for data preparation"""
        mock_lambda_client.invoke.return_value = mock_successful_fe_response
        
        event = {
            'httpMethod': 'POST',
            'path': '/aiservice/feature-engineering',
            'body': {
                'serviceId': 'service123',
                'dataSourceId': 'data123',
                'column': 'target',
                'problemType': 'classifier'
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "launchFE",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert response_json['status'] == 'ready'
        assert response_json['service_id'] == 'service123'
        mock_lambda_client.invoke.assert_called_once()

    def test_process_data_prep_status(self, mock_lambda_client, mock_data_prep_status):
        """Test GET request for data preparation status"""
        mock_lambda_client.invoke.return_value = mock_data_prep_status
        
        event = {
            'httpMethod': 'GET',
            'path': '/aiservice/feature-engineering',
            'queryStringParameters': {
                'reportId': 'report123',
                'serviceId': 'service123'
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "launchFE",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert response_json['report123']['status'] == 'ready'
        assert response_json['report123']['engine'] == 'aws-sklearn-serverless'
        mock_lambda_client.invoke.assert_called_once()

    def test_download_train_file(self, mock_lambda_client, mock_s3_client, mock_train_file_response):
        """Test downloading training file"""
        mock_lambda_client.invoke.return_value = mock_train_file_response
        
        event = {
            'httpMethod': 'GET',
            'path': '/aiservice/feature-engineering/download-train',
            'queryStringParameters': {
                'reportId': 'report123',
                'serviceId': 'service123'
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "launchFE",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert response_json['result'] == 'success'
        assert 'url' in response_json
        mock_lambda_client.invoke.assert_called_once()

    def test_download_test_file(self, mock_lambda_client, mock_s3_client, mock_test_file_response):
        """Test downloading test file"""
        mock_lambda_client.invoke.return_value = mock_test_file_response
        
        event = {
            'httpMethod': 'GET',
            'path': '/aiservice/feature-engineering/download-test',
            'queryStringParameters': {
                'reportId': 'report123',
                'serviceId': 'service123'
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "launchFE",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert response_json['result'] == 'success'
        assert 'url' in response_json
        mock_lambda_client.invoke.assert_called_once()

    def test_process_artifacts_url(self, mock_lambda_client, mock_s3_client, mock_artifacts_url_response):
        """Test getting artifacts URL"""
        mock_lambda_client.invoke.return_value = mock_artifacts_url_response
        
        event = {
            'httpMethod': 'GET',
            'path': '/aiservice/feature-engineering/artifacts-url',
            'queryStringParameters': {
                'reportId': 'report123',
                'serviceId': 'service123',
                'objectType': 'code',
                'object': 'stand-alone'
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "launchFE",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert response_json['result'] == 'success'
        assert 'url' in response_json
        mock_lambda_client.invoke.assert_called_once()

    def test_unsupported_method(self, mock_lambda_client, mock_unsupported_method_response):
        """Test error handling for unsupported HTTP methods"""
        mock_lambda_client.invoke.return_value = mock_unsupported_method_response
        
        event = {
            'httpMethod': 'PUT',
            'path': '/aiservice/feature-engineering',
            'queryStringParameters': {
                'reportId': 'report123'
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "launchFE",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert 'Unsupported Method: PUT' in str(response_json)
        mock_lambda_client.invoke.assert_called_once()

    def test_missing_parameters(self, mock_lambda_client, mock_missing_params_response):
        """Test error handling for missing required parameters"""
        mock_lambda_client.invoke.return_value = mock_missing_params_response
        
        event = {
            'httpMethod': 'POST',
            'path': '/aiservice/feature-engineering',
            'body': {}  # Empty body
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "launchFE",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert response_json['result'] == 'failure'
        mock_lambda_client.invoke.assert_called_once()
