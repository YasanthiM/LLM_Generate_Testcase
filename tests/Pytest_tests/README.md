# Pytest Test Suite for Windsurf

This directory contains the test suite for various Lambda functions and services in the Windsurf project. The tests are written using pytest and focus on testing the API interfaces and functionality of each service.

## Test Files Overview

### 1. test_train_experiments.py
Tests for training experiments Lambda function:
- `TestTrainExperiments`
  - `test_get_experiment`: Test retrieving experiment details
  - `test_post_experiment`: Test creating new experiments
  - `test_patch_experiment`: Test updating experiment details
  - `test_delete_experiment`: Test removing experiments
  - `test_get_experiment_with_filters`: Test filtering experiments
  - `test_error_handling`: Test error cases

### 2. test_retrain.py
Tests for model retraining functionality:
- `TestRetrain`
  - `test_get_retrain_experiment`: Test retrieving retrain details
  - `test_launch_retrain`: Test launching retraining
  - `test_patch_retrain`: Test updating retrain status
  - `test_delete_retrain`: Test removing retrain experiments
  - `test_get_retrain_superuser`: Test superuser access
  - `test_error_handling`: Test error cases

### 3. test_launch_fe.py
Tests for frontend launch functionality:
- `TestLaunchFE`
  - `test_process_data_prep_post_request`: Test data preparation
  - `test_process_data_prep_status`: Test preparation status
  - `test_download_train_file`: Test training file download
  - `test_download_test_file`: Test test file download
  - `test_process_artifacts_url`: Test artifacts URL generation
  - `test_unsupported_method`: Test method validation
  - `test_missing_parameters`: Test parameter validation

### 4. test_train.py
Tests for model training functionality:
- `TestTrain`
  - `test_fetch_logs`: Test log retrieval
  - `test_code_generator`: Test AI code generation
  - `test_train_import_post`: Test training import
  - `test_train_import_get`: Test import status
  - `test_launch_train`: Test training launch
  - `test_train_status`: Test training status
  - `test_train_params`: Test parameter handling
  - `test_error_handling`: Test error cases

### 5. test_aiservice.py
Tests for AI service management:
- `TestAiService`
  - `test_get_service_by_id`: Test service lookup by ID
  - `test_get_service_by_name`: Test service lookup by name
  - `test_super_user_access`: Test superuser permissions
  - `test_create_service`: Test service creation
  - `test_update_service`: Test service updates
  - `test_delete_service`: Test service deletion
  - `test_list_services`: Test service listing
  - `test_error_handling`: Test error cases

### Additional Test Files
- `test_ask_ai.py`
- `test_dashboard.py`
- `test_launch_train.py`

These files are currently in development or pending implementation.

## Running Tests

To run all tests:
```bash
python -m pytest tests/Pytest_tests -v
```

To run a specific test file:
```bash
python -m pytest tests/Pytest_tests/test_file_name.py -v
```

## Test Structure
Each test file follows a consistent pattern:
1. Mock fixtures for AWS services (Lambda, S3)
2. Mock response fixtures for different scenarios
3. Test classes containing test methods
4. Comprehensive validation of:
   - HTTP methods (GET, POST, PATCH, DELETE)
   - Success and error cases
   - Input validation
   - Response format validation
   - Special permissions
   - Edge cases
