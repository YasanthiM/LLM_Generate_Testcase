# AskAI Lambda Function Tests

This repository contains test cases for the AskAI Lambda function.

## Project Structure
```
.
├── tests/
│   ├── __init__.py
│   └── test_ask_ai.py
├── requirements.txt
└── README.md
```

## Test Cases

The test suite includes the following test cases:

1. `test_ask_ai_with_service_id`: Tests the function with a service ID
2. `test_ask_ai_with_prediction_id`: Tests the function with a prediction ID
3. `test_ask_ai_with_timestamps`: Tests the function with timestamp filters
4. `test_ask_ai_monitor_mode`: Tests the monitor mode for super users
5. `test_ask_ai_missing_required_params`: Tests error handling for missing parameters

## Running Tests

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run tests:
```bash
pytest tests/test_ask_ai.py -v
```
