# Configuration variables for test files
FUNCTION_NAME_PREFIX = "yasanthi_"

# AWS configurations
AWS_REGION = "us-east-1"  # Default AWS region
DEFAULT_WAIT_TIME = {
    "aws-sklearn-serverless": 60,
    "aws-sagemaker": 300
}

# Common test data
DEFAULT_USER_ID = "ai_gym"
DEFAULT_CLASS_ID = "test_class"

# API endpoints and prefixes
API_GATEWAY_URL = "https://api.example.com/v1"  # Replace with actual API URL if needed
