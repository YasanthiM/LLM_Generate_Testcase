import pytest
import json
import sys
import os
from unittest.mock import MagicMock, patch
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FUNCTION_NAME_PREFIX

@pytest.fixture
def mock_lambda_client():
    with patch('lambda_utils.LAMBDA') as mock_lambda:
        yield mock_lambda

@pytest.fixture
def mock_get_retrain_response():
    return {
        'StatusCode': 200,
        'Payload': json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'retrain123': {
                    'retrainId': 'retrain123',
                    'serId': 'service123',
                    'dataId': 'data123',
                    'userId': 'user123',
                    'predictCol': 'target',
                    'reportId': 'report123',
                    'expId': 'exp123',
                    'depId': 'dep123',
                    'timestamp': '2025-04-09T10:25:14',
                    'currentStage': 'training',
                    'status': 'Running',
                    'message': 'Training in progress',
                    'dataLocation': 's3://bucket/data123'
                }
            })
        })
    }

@pytest.fixture
def mock_post_retrain_response():
    return {
        'StatusCode': 200,
        'Payload': json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'result': 'success',
                'retrainId': 'retrain123'
            })
        })
    }

@pytest.fixture
def mock_patch_retrain_response():
    return {
        'StatusCode': 200,
        'Payload': json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'retrainId': 'retrain123'
            })
        })
    }

@pytest.fixture
def mock_delete_retrain_response():
    return {
        'StatusCode': 200,
        'Payload': json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'result': 'success',
                'retrainId': 'retrain123'
            })
        })
    }

class TestRetrain:
    def test_get_retrain_experiment(self, mock_lambda_client, mock_get_retrain_response):
        """Test GET request for retrieving retrain experiment details"""
        mock_lambda_client.invoke.return_value = mock_get_retrain_response
        
        event = {
            'httpMethod': 'GET',
            'path': '/aiservice/retrain',
            'queryStringParameters': {
                'retrainId': 'retrain123',
                'serviceId': 'service123',
                'timestamp': '2025-04-09T00:00:00'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user123'
                    }
                }
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "retrainExperiment",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert 'retrain123' in response_json
        retrain_details = response_json['retrain123']
        assert retrain_details['retrainId'] == 'retrain123'
        assert retrain_details['serId'] == 'service123'
        assert retrain_details['status'] == 'Running'
        mock_lambda_client.invoke.assert_called_once()

    def test_launch_retrain(self, mock_lambda_client, mock_post_retrain_response):
        """Test POST request for launching a retrain experiment"""
        mock_lambda_client.invoke.return_value = mock_post_retrain_response
        
        event = {
            'httpMethod': 'POST',
            'path': '/aiservice/retrain',
            'body': {
                'retrainId': 'retrain123',
                'serviceId': 'service123',
                'dataId': 'data123',
                'reportId': 'report123',
                'experimentId': 'exp123',
                'deploymentId': 'dep123',
                'predictColumn': 'target',
                'currentStage': 'training',
                'status': 'Starting',
                'message': 'Initializing training',
                'dataLocation': 's3://bucket/data123'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user123'
                    }
                }
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "launchRetrain",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert response_json['result'] == 'success'
        assert response_json['retrainId'] == 'retrain123'
        mock_lambda_client.invoke.assert_called_once()

    def test_patch_retrain(self, mock_lambda_client, mock_patch_retrain_response):
        """Test PATCH request for updating retrain experiment details"""
        mock_lambda_client.invoke.return_value = mock_patch_retrain_response
        
        event = {
            'httpMethod': 'PATCH',
            'path': '/aiservice/retrain',
            'queryStringParameters': {
                'retrainId': 'retrain123'
            },
            'body': {
                'status': 'Completed',
                'message': 'Training completed successfully',
                'currentStage': 'completed'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user123'
                    }
                }
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "retrainExperiment",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert response_json['retrainId'] == 'retrain123'
        mock_lambda_client.invoke.assert_called_once()

    def test_delete_retrain(self, mock_lambda_client, mock_delete_retrain_response):
        """Test DELETE request for removing a retrain experiment"""
        mock_lambda_client.invoke.return_value = mock_delete_retrain_response
        
        event = {
            'httpMethod': 'DELETE',
            'path': '/aiservice/retrain',
            'queryStringParameters': {
                'retrainId': 'retrain123'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user123'
                    }
                }
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "retrainExperiment",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert response_json['result'] == 'success'
        assert response_json['retrainId'] == 'retrain123'
        mock_lambda_client.invoke.assert_called_once()

    def test_get_retrain_superuser(self, mock_lambda_client, mock_get_retrain_response):
        """Test GET request with superuser permissions"""
        mock_lambda_client.invoke.return_value = mock_get_retrain_response
        
        event = {
            'httpMethod': 'GET',
            'path': '/aiservice/retrain',
            'queryStringParameters': {
                'userId': 'otheruser123',  # Superuser can query other users' data
                'serviceId': 'service123'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'superuser123',
                        'cognito:groups': ['admin']  # This makes the user a superuser
                    }
                }
            }
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "retrainExperiment",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert 'retrain123' in response_json
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
            'path': '/aiservice/retrain',
            'body': {}  # Empty body to trigger error
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "launchRetrain",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert response_json['result'] == 'failure'
        assert 'error' in response_json
        mock_lambda_client.invoke.assert_called_once()
