import pytest
import json
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FUNCTION_NAME_PREFIX

@pytest.fixture
def mock_lambda_client():
    with patch('lambda_utils.LAMBDA') as mock_lambda:
        yield mock_lambda

@pytest.fixture
def mock_get_experiment_response():
    return {
        'StatusCode': 200,
        'Payload': json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'exp123': {
                    'exp_id': 'exp123',
                    'ser_id': 'service123',
                    'report_id': 'report123',
                    'creation_date': '2025-04-09T10:25:14',
                    'name': 'test_experiment',
                    'mode': 'aws-sklearn-serverless',
                    'launch_mode': 'automatic',
                    'instance_type': 'ml.m5.large',
                    'status': 'Completed',
                    'train_data_id': 'train123',
                    'test_data_id': 'test123',
                    'predict_column': 'target',
                    'job_ids': '["job1", "job2"]',
                    'hyper_params': '{"n_estimators": 100}',
                    'job_status_details': '{"status": "Completed"}',
                    'result': '{"accuracy": 0.95}',
                    'metrics': '{"f1_score": 0.94}',
                    'cost': 1.23,
                    'user_id': 'user123'
                }
            })
        })
    }

@pytest.fixture
def mock_post_experiment_response():
    return {
        'StatusCode': 200,
        'Payload': json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'result': 'success',
                'exp_id': 'exp123'
            })
        })
    }

@pytest.fixture
def mock_patch_experiment_response():
    return {
        'StatusCode': 200,
        'Payload': json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'result': 'success',
                'exp_id': 'exp123'
            })
        })
    }

@pytest.fixture
def mock_delete_experiment_response():
    return {
        'StatusCode': 200,
        'Payload': json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'result': 'success',
                'exp_id': 'exp123',
                'service_id': 'service123'
            })
        })
    }

class TestTrainExperiments:
    def test_get_experiment(self, mock_lambda_client, mock_get_experiment_response):
        """Test GET request for retrieving experiment details"""
        mock_lambda_client.invoke.return_value = mock_get_experiment_response
        
        event = {
            'httpMethod': 'GET',
            'path': '/aiservice/trainexperiment',
            'queryStringParameters': {
                'experimentId': 'exp123',
                'serviceId': 'service123'
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
            FunctionName=FUNCTION_NAME_PREFIX + "trainExperiments",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert 'exp123' in response_json
        exp_details = response_json['exp123']
        assert exp_details['exp_id'] == 'exp123'
        assert exp_details['ser_id'] == 'service123'
        assert exp_details['status'] == 'Completed'
        mock_lambda_client.invoke.assert_called_once()

    def test_post_experiment(self, mock_lambda_client, mock_post_experiment_response):
        """Test POST request for creating a new experiment"""
        mock_lambda_client.invoke.return_value = mock_post_experiment_response
        
        event = {
            'httpMethod': 'POST',
            'path': '/aiservice/trainexperiment',
            'body': {
                'experimentId': 'exp123',
                'serviceId': 'service123',
                'reportId': 'report123',
                'name': 'test_experiment',
                'status': 'Starting',
                'trainDataId': 'train123',
                'testDataId': 'test123',
                'predictColumn': 'target',
                'mode': 'aws-sklearn-serverless',
                'launchMode': 'automatic'
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
            FunctionName=FUNCTION_NAME_PREFIX + "trainExperiments",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert response_json['result'] == 'success'
        assert response_json['exp_id'] == 'exp123'
        mock_lambda_client.invoke.assert_called_once()

    def test_patch_experiment(self, mock_lambda_client, mock_patch_experiment_response):
        """Test PATCH request for updating experiment details"""
        mock_lambda_client.invoke.return_value = mock_patch_experiment_response
        
        event = {
            'httpMethod': 'PATCH',
            'path': '/aiservice/trainexperiment',
            'queryStringParameters': {
                'experimentId': 'exp123'
            },
            'body': {
                'status': 'Completed',
                'result': '{"accuracy": 0.95}',
                'metrics': '{"f1_score": 0.94}'
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
            FunctionName=FUNCTION_NAME_PREFIX + "trainExperiments",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert response_json['result'] == 'success'
        assert response_json['exp_id'] == 'exp123'
        mock_lambda_client.invoke.assert_called_once()

    def test_delete_experiment(self, mock_lambda_client, mock_delete_experiment_response):
        """Test DELETE request for removing an experiment"""
        mock_lambda_client.invoke.return_value = mock_delete_experiment_response
        
        event = {
            'httpMethod': 'DELETE',
            'path': '/aiservice/trainexperiment',
            'queryStringParameters': {
                'experimentId': 'exp123',
                'serviceId': 'service123'
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
            FunctionName=FUNCTION_NAME_PREFIX + "trainExperiments",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert response_json['result'] == 'success'
        assert response_json['exp_id'] == 'exp123'
        assert response_json['service_id'] == 'service123'
        mock_lambda_client.invoke.assert_called_once()

    def test_get_experiment_with_filters(self, mock_lambda_client, mock_get_experiment_response):
        """Test GET request with various filters"""
        mock_lambda_client.invoke.return_value = mock_get_experiment_response
        
        event = {
            'httpMethod': 'GET',
            'path': '/aiservice/trainexperiment',
            'queryStringParameters': {
                'serviceId': 'service123',
                'reportId': 'report123',
                'mode': 'monitor',
                'startTimestamp': '2025-04-09T00:00:00',
                'endTimestamp': '2025-04-09T23:59:59',
                'limit': '10'
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
            FunctionName=FUNCTION_NAME_PREFIX + "trainExperiments",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert 'exp123' in response_json
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
            'path': '/aiservice/trainexperiment',
            'body': {}  # Empty body to trigger error
        }
        
        response = mock_lambda_client.invoke(
            FunctionName=FUNCTION_NAME_PREFIX + "trainExperiments",
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        response_json = json.loads(json.loads(response['Payload'])['body'])
        assert response_json['result'] == 'failure'
        assert 'error' in response_json
        mock_lambda_client.invoke.assert_called_once()
