import boto3
import json
import lambda_utils as lutils

FUNCTION_NAME_PREFIX = "yasanthi_"

LAMBDA = boto3.client("lambda")

def test_launchTrain():
    test_cases = [
        {
            "name": "Valid input with automatic launch mode",
            "body": {
                "body": json.dumps({
                    "serviceId": "service123",
                    "launchMode": "automatic",
                    "mode": "aws-sklearn-serverless"
                })
            },
            "expected": {
                "status": "success",
                "data_contains": ["experimentId", "serviceId", "waitTime", "user", "launchMode"],
                "errors": []
            }
        },
        {
            "name": "Valid input with manual launch mode",
            "body": {
                "body": json.dumps({
                    "serviceId": "service456",
                    "launchMode": "manual",
                    "mode": "aws-tensorflow-serverless"
                })
            },
            "expected": {
                "status": "success",
                "data_contains": ["experimentId", "serviceId", "waitTime", "user", "launchMode"],
                "errors": []
            }
        },
    ]

    for test in test_cases:
        response = lutils.invoke_lambda(FUNCTION_NAME_PREFIX + "launchTrain", body=test["body"])

        # Ensure response is a dictionary
        if isinstance(response, str):
            try:
                response_json = json.loads(response)  # Convert string to dict if needed
            except json.JSONDecodeError:
                print(f"{test['name']}: Failed - Response is not valid JSON")
                continue
        else:
            response_json = response  # Already a dict, use it directly

        # Extract "body" if it exists and is a string
        if "body" in response_json and isinstance(response_json["body"], str):
            try:
                response_json = json.loads(response_json["body"])  # Convert inner JSON string to dict
            except json.JSONDecodeError:
                print(f"{test['name']}: Failed - Response body is not valid JSON")
                continue

        expected = test["expected"]
        if (
            response_json.get("status") == expected["status"] and
            all(key in response_json.get("data", {}) for key in expected.get("data_contains", [])) and
            response_json.get("errors") == expected["errors"]
        ):
            print(f"{test['name']}: Passed")
        else:
            print(f"{test['name']}: Failed - Expected {expected}, got {response_json}")

# Run the test
test_launchTrain()