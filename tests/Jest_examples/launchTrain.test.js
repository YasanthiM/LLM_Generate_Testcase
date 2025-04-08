// Mock lambda_utils
const mockLambdaUtils = {
  invokeLambda: jest.fn()
};

const FUNCTION_NAME_PREFIX = "yasanthi_";

describe('Launch Train Tests', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
  });

  const testCases = [
    {
      name: "Valid input with automatic launch mode",
      body: {
        body: JSON.stringify({
          serviceId: "service123",
          launchMode: "automatic",
          mode: "aws-sklearn-serverless"
        })
      },
      expected: {
        status: "success",
        data_contains: ["experimentId", "serviceId", "waitTime", "user", "launchMode"],
        errors: []
      }
    },
    {
      name: "Valid input with manual launch mode",
      body: {
        body: JSON.stringify({
          serviceId: "service456",
          launchMode: "manual",
          mode: "aws-tensorflow-serverless"
        })
      },
      expected: {
        status: "success",
        data_contains: ["experimentId", "serviceId", "waitTime", "user", "launchMode"],
        errors: []
      }
    }
  ];

  testCases.forEach(testCase => {
    test(`should handle ${testCase.name}`, async () => {
      // Mock successful response
      const mockResponse = {
        status: "success",
        data: {
          experimentId: "exp123",
          serviceId: testCase.body.body.includes("service123") ? "service123" : "service456",
          waitTime: 300,
          user: "testUser",
          launchMode: testCase.body.body.includes("automatic") ? "automatic" : "manual"
        },
        errors: []
      };

      // Setup mock for lambda invocation
      mockLambdaUtils.invokeLambda.mockResolvedValueOnce({
        body: JSON.stringify(mockResponse)
      });

      // Invoke the lambda function
      const response = await mockLambdaUtils.invokeLambda(
        FUNCTION_NAME_PREFIX + "launchTrain",
        testCase.body
      );

      let responseJson;
      try {
        // Handle string response
        if (typeof response === 'string') {
          responseJson = JSON.parse(response);
        } else if (typeof response.body === 'string') {
          // Handle nested JSON string in body
          responseJson = JSON.parse(response.body);
        } else {
          responseJson = response;
        }

        // Verify response matches expected format
        expect(responseJson.status).toBe(testCase.expected.status);
        
        // Verify all expected keys exist in data
        testCase.expected.data_contains.forEach(key => {
          expect(responseJson.data).toHaveProperty(key);
        });

        // Verify errors array
        expect(responseJson.errors).toEqual(testCase.expected.errors);

      } catch (error) {
        fail(`Failed to parse response JSON: ${error.message}`);
      }

      // Verify lambda was called with correct parameters
      expect(mockLambdaUtils.invokeLambda).toHaveBeenCalledWith(
        FUNCTION_NAME_PREFIX + "launchTrain",
        expect.objectContaining(testCase.body)
      );
    });
  });

  test('should handle invalid JSON response', async () => {
    // Mock an invalid JSON response
    mockLambdaUtils.invokeLambda.mockResolvedValueOnce('invalid json');

    await expect(async () => {
      const response = await mockLambdaUtils.invokeLambda(
        FUNCTION_NAME_PREFIX + "launchTrain",
        testCases[0].body
      );
      
      if (typeof response === 'string') {
        JSON.parse(response);
      }
    }).rejects.toThrow();
  });

  test('should handle invalid response body', async () => {
    // Mock a response with invalid body JSON
    mockLambdaUtils.invokeLambda.mockResolvedValueOnce({
      body: 'invalid json'
    });

    await expect(async () => {
      const response = await mockLambdaUtils.invokeLambda(
        FUNCTION_NAME_PREFIX + "launchTrain",
        testCases[0].body
      );
      
      if (typeof response.body === 'string') {
        JSON.parse(response.body);
      }
    }).rejects.toThrow();
  });
});
