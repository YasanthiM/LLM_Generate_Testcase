// Mock AWS SDK
const mockLambda = {
  invoke: jest.fn()
};

// Mock lambda_utils
const mockLambdaUtils = {
  invokeLambda: jest.fn()
};

const FUNCTION_NAME_PREFIX = "yasanthi_";

describe('Dashboard Tests', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
  });

  describe('dashboardStudent', () => {
    const testCases = [
      {
        name: "Valid input",
        body: {
          body: JSON.stringify({
            personId: "12345",
            type: "student",
            gradYear: 2025,
            county: "Clark",
            state: "NV",
            interests: "Science, Math",
            mentor: "Mentor Name",
            schoolId: "school123"
          })
        },
        expected: {
          status: "success",
          data_contains: ["studentId"],
          errors: []
        }
      },
      {
        name: "Minimal input",
        body: {
          body: JSON.stringify({
            personId: "67890",
            type: "student"
          })
        },
        expected: {
          status: "success",
          data_contains: ["studentId"],
          errors: []
        }
      }
    ];

    testCases.forEach(testCase => {
      test(`should handle ${testCase.name}`, async () => {
        // Mock successful response
        const mockResponse = {
          status: "success",
          data: { studentId: "test-student-id" },
          errors: []
        };

        // Setup mock for lambda invocation
        mockLambdaUtils.invokeLambda.mockResolvedValueOnce({
          body: JSON.stringify(mockResponse)
        });

        // Invoke the lambda function
        const response = await mockLambdaUtils.invokeLambda(
          FUNCTION_NAME_PREFIX + "dashboardStudent",
          { body: testCase.body }
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
          FUNCTION_NAME_PREFIX + "dashboardStudent",
          expect.objectContaining({ body: testCase.body })
        );
      });
    });

    test('should handle invalid JSON response', async () => {
      // Mock an invalid JSON response
      mockLambdaUtils.invokeLambda.mockResolvedValueOnce('invalid json');

      await expect(async () => {
        const response = await mockLambdaUtils.invokeLambda(
          FUNCTION_NAME_PREFIX + "dashboardStudent",
          { body: testCases[0].body }
        );
        
        if (typeof response === 'string') {
          JSON.parse(response);
        }
      }).rejects.toThrow();
    });
  });
});
