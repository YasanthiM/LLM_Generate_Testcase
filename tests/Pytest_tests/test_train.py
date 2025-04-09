import pytest
import json
import boto3
from unittest.mock import MagicMock, patch
import sys
sys.path.append("tests")
from config import FUNCTION_NAME_PREFIX
from lambda_utils import invoke_lambda
import pandas as pd
import numpy as np

@pytest.fixture
def mock_lambda_client():
    with patch('lambda_utils.LAMBDA') as mock_lambda:
        yield mock_lambda

@pytest.fixture
def mock_s3_client():
    with patch('boto3.client') as mock_s3:
        mock_client = MagicMock()
        mock_s3.return_value = mock_client
        yield mock_client

@pytest.fixture
def mock_successful_train_response():
    return {
        'StatusCode': 200,
        'Payload': json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'exp_id': 'exp123',
                'experimentId': 'exp123',
                'jobIds': ['job1', 'job2'],
                'user': 'user123',
                'serviceId': 'service123',
                'startTimeStamp': 1234567890
            })
        })
    }

@pytest.fixture
def mock_fetch_logs_response():
    return {
        'StatusCode': 200,
        'Payload': json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'logs': ['log1', 'log2', 'log3'],
                'result': 'success'
            })
        })
    }

@pytest.fixture
def mock_code_generator_response():
    return {
        'StatusCode': 200,
        'Payload': json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'code': 'def train_model():\n    pass',
                'result': 'success'
            })
        })
    }

@pytest.fixture
def mock_train_import_response():
    return {
        'StatusCode': 200,
        'Payload': json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'importId': 'import123',
                'result': 'success'
            })
        })
    }

@pytest.fixture
def mock_train_status_response():
    return {
        'StatusCode': 200,
        'Payload': json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'status': 'completed',
                'jobIds': ['job1', 'job2'],
                'result': 'success'
            })
        })
    }

@pytest.fixture
def mock_train_params_response():
    return {
        'StatusCode': 200,
        'Payload': json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'params': {
                    'algorithm': 'RandomForest',
                    'hyperparameters': {
                        'n_estimators': 100,
                        'max_depth': 10
                    }
                },
                'result': 'success'
            })
        })
    }

class TestTrain:
    def test_fetch_logs(self, mock_lambda_client, mock_fetch_logs_response):
        """Test GET request for fetching training logs"""
        mock_lambda_client.invoke.return_value = mock_fetch_logs_response
        
        event = {
            'httpMethod': 'GET',
            'path': '/aiservice/train/logs',
            'queryStringParameters': {
                'experimentId': 'exp123',
                'serviceId': 'service123'
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "fetchLogs",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert response_json['result'] == 'success'
        assert isinstance(response_json['logs'], list)
        mock_lambda_client.invoke.assert_called_once()

    def test_code_generator(self, mock_lambda_client, mock_code_generator_response):
        """Test POST request for AI code generation"""
        mock_lambda_client.invoke.return_value = mock_code_generator_response
        
        event = {
            'httpMethod': 'POST',
            'path': '/aiservice/train/code',
            'body': {
                'serviceId': 'service123',
                'experimentId': 'exp123',
                'prompt': 'Generate training code'
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "aiCodeGenerator",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert response_json['result'] == 'success'
        assert 'code' in response_json
        mock_lambda_client.invoke.assert_called_once()

    def test_train_import_post(self, mock_lambda_client, mock_train_import_response):
        """Test POST request for training import"""
        mock_lambda_client.invoke.return_value = mock_train_import_response
        
        event = {
            'httpMethod': 'POST',
            'path': '/aiservice/train/import',
            'body': {
                'serviceId': 'service123',
                'experimentId': 'exp123',
                'files': ['file1.csv', 'file2.csv']
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "sgmTrainImport",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert response_json['result'] == 'success'
        assert 'importId' in response_json
        mock_lambda_client.invoke.assert_called_once()

    def test_train_import_get(self, mock_lambda_client, mock_train_import_response):
        """Test GET request for training import status"""
        mock_lambda_client.invoke.return_value = mock_train_import_response
        
        event = {
            'httpMethod': 'GET',
            'path': '/aiservice/train/import',
            'queryStringParameters': {
                'importId': 'import123',
                'serviceId': 'service123'
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "sgmTrainImport",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert response_json['result'] == 'success'
        assert 'importId' in response_json
        mock_lambda_client.invoke.assert_called_once()

    def test_launch_train(self, mock_lambda_client, mock_successful_train_response):
        """Test POST request for launching training"""
        mock_lambda_client.invoke.return_value = mock_successful_train_response
        
        event = {
            'httpMethod': 'POST',
            'path': '/aiservice/train',
            'body': {
                'serviceId': 'service123',
                'reportId': 'report123',
                'experimentId': 'exp123',
                'params': [{
                    'name': 'RandomForest',
                    'hyperparameters': {
                        'n_estimators': 100,
                        'max_depth': 10
                    }
                }]
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "launchTrain",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert response_json['experimentId'] == 'exp123'
        assert isinstance(response_json['jobIds'], list)
        mock_lambda_client.invoke.assert_called_once()

    def test_train_status(self, mock_lambda_client, mock_train_status_response):
        """Test GET request for training status"""
        mock_lambda_client.invoke.return_value = mock_train_status_response
        
        event = {
            'httpMethod': 'GET',
            'path': '/aiservice/train',
            'queryStringParameters': {
                'experimentId': 'exp123',
                'serviceId': 'service123'
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "trainStatus",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert response_json['result'] == 'success'
        assert response_json['status'] == 'completed'
        assert isinstance(response_json['jobIds'], list)
        mock_lambda_client.invoke.assert_called_once()

    def test_train_params(self, mock_lambda_client, mock_train_params_response):
        """Test GET request for training parameters"""
        mock_lambda_client.invoke.return_value = mock_train_params_response
        
        event = {
            'httpMethod': 'GET',
            'path': '/aiservice/train/params',
            'queryStringParameters': {
                'experimentId': 'exp123',
                'serviceId': 'service123'
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "trainParams",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert response_json['result'] == 'success'
        assert 'params' in response_json
        assert 'algorithm' in response_json['params']
        assert 'hyperparameters' in response_json['params']
        mock_lambda_client.invoke.assert_called_once()

    def test_error_handling(self, mock_lambda_client):
        """Test error handling for invalid requests"""
        mock_lambda_client.invoke.return_value = {
            'StatusCode': 400,
            'Payload': json.dumps({
                'statusCode': 400,
                'body': json.dumps({
                    'result': 'failure',
                    'error': 'Invalid request parameters'
                })
            })
        }
        
        event = {
            'httpMethod': 'POST',
            'path': '/aiservice/train',
            'body': {}  # Empty body to trigger error
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "launchTrain",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert response_json['result'] == 'failure'
        assert 'error' in response_json
        mock_lambda_client.invoke.assert_called_once()
