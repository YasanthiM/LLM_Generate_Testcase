// Mock utilities and dependencies
const mockDBUtils = {
  extractId: jest.fn((event, key) => event?.queryStringParameters?.[key]),
  executeStatement: jest.fn((statement) => [{
    prediction_id: 'pred123',
    ser_id: 'ser123',
    timestamp: '2025-03-24T13:10:23'
  }]),
  prepareGetResponse: jest.fn((serviceName, response) => ({
    status: 'success',
    data: response,
    errors: []
  }))
};

const mockReqUtils = {
  isSuperUser: jest.fn((event) => event?.is_super_user || false)
};

// Setup mocks and dependencies
const dbutils = mockDBUtils;
const req_utils = mockReqUtils;
const TABLE_NAME = "ask_ai_table";

// Function to test
function processGetRequest(event) {
  const ser_id = dbutils.extractId(event, 'serviceId');
  const prediction_id = dbutils.extractId(event, 'predictionId');
  const mode = dbutils.extractId(event, 'mode');
  const start_timestamp = dbutils.extractId(event, 'startTimestamp');
  const end_timestamp = dbutils.extractId(event, 'endTimestamp');

  if (!ser_id && !prediction_id && !(mode === 'monitor' && req_utils.isSuperUser(event))) {
    return 'please provide serviceId or predictionId';
  }

  let statement = `select * from ${TABLE_NAME}`;
  const queries = [];

  if (ser_id) {
    queries.push(` ser_id="${ser_id}"`);
  } else if (prediction_id) {
    queries.push(` prediction_id="${prediction_id}"`);
  }
  if (start_timestamp) {
    queries.push(` timestamp > "${start_timestamp}"`);
  }
  if (end_timestamp) {
    queries.push(` timestamp <= "${end_timestamp}"`);
  }

  queries.forEach((query, index) => {
    statement += index === 0 ? " where" + query : " and" + query;
  });

  if (!queries.length) {
    const order_stmt = " order by timestamp desc limit 100";
    statement += order_stmt;
  }

  const stmt_response = dbutils.executeStatement(statement);
  return dbutils.prepareGetResponse('askAI', stmt_response);
}

describe('AskAI Tests', () => {
  test('should process request with service ID', () => {
    const event = {
      queryStringParameters: {
        serviceId: 'ser123'
      }
    };
    
    const response = processGetRequest(event);
    expect(response.status).toBe('success');
    expect(response.data.length).toBeGreaterThan(0);
    expect(response.data[0].ser_id).toBe('ser123');
  });

  test('should process request with prediction ID', () => {
    const event = {
      queryStringParameters: {
        predictionId: 'pred123'
      }
    };
    
    const response = processGetRequest(event);
    expect(response.status).toBe('success');
    expect(response.data.length).toBeGreaterThan(0);
    expect(response.data[0].prediction_id).toBe('pred123');
  });

  test('should process request with timestamps', () => {
    const event = {
      queryStringParameters: {
        serviceId: 'ser123',
        startTimestamp: '2025-03-24T12:00:00',
        endTimestamp: '2025-03-24T14:00:00'
      }
    };
    
    const response = processGetRequest(event);
    expect(response.status).toBe('success');
    expect(response.data.length).toBeGreaterThan(0);
  });

  test('should process monitor mode request for super user', () => {
    const event = {
      queryStringParameters: {
        mode: 'monitor'
      },
      is_super_user: true
    };
    
    const response = processGetRequest(event);
    expect(response.status).toBe('success');
  });

  test('should handle missing required parameters', () => {
    const event = {
      queryStringParameters: {}
    };
    
    const response = processGetRequest(event);
    expect(response).toBe('please provide serviceId or predictionId');
  });
});
