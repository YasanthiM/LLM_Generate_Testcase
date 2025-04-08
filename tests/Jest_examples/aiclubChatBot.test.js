// Mock OpenAI
const mockOpenAI = {
  moderations: {
    create: jest.fn()
  },
  chat: {
    completions: {
      create: jest.fn()
    }
  }
};

// Mock Utils
const mockRequestUtils = {
  prepare_process_event: jest.fn()
};

const mockResponseUtils = {
  success_response: jest.fn(data => ({ 
    statusCode: 200, 
    body: JSON.stringify(data) 
  })),
  success_method: jest.fn(),
  unsupported_method: jest.fn()
};

const mockRouter = {
  path_router: jest.fn(),
  route: jest.fn()
};

// Constants from the original code
const MESSAGES = [
  {
    role: "system",
    content: "The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly. You are named as Chai Bot."
  },
  {
    role: "user",
    content: "Hello, who are you?"
  },
  {
    role: "assistant",
    content: "I am Chai Bot! an AI created by AIClub. How can I help you today?"
  }
];

const INAPPROPRIATE_QUESTION = "Sorry, I am only capable of answering friendly questions. Please try again.";
const INAPPROPRIATE_CONTENT = "Ouch! Answer is too sensitive. PLease try another question.";

describe('AIClub ChatBot Tests', () => {
  beforeEach(() => {
    // Clear all mocks
    jest.clearAllMocks();
    
    // Reset mock implementations
    mockOpenAI.moderations.create.mockReset();
    mockOpenAI.chat.completions.create.mockReset();
  });

  describe('filterContent', () => {
    test('should return true for inappropriate content', async () => {
      mockOpenAI.moderations.create.mockResolvedValueOnce({
        results: [{ flagged: true }]
      });

      const result = await filterContent('inappropriate content');
      expect(result).toBe(true);
      expect(mockOpenAI.moderations.create).toHaveBeenCalledWith({
        input: 'inappropriate content'
      });
    });

    test('should return false for appropriate content', async () => {
      mockOpenAI.moderations.create.mockResolvedValueOnce({
        results: [{ flagged: false }]
      });

      const result = await filterContent('appropriate content');
      expect(result).toBe(false);
      expect(mockOpenAI.moderations.create).toHaveBeenCalledWith({
        input: 'appropriate content'
      });
    });
  });

  describe('processPostRequest', () => {
    const mockEvent = {
      body: {
        question: 'What is AI?',
        max_tokens: 100
      }
    };

    test('should handle inappropriate questions', async () => {
      mockOpenAI.moderations.create.mockResolvedValueOnce({
        results: [{ flagged: true }]
      });

      const response = await processPostRequest(mockEvent);
      expect(response.statusCode).toBe(200);
      expect(JSON.parse(response.body)).toEqual({
        answers: INAPPROPRIATE_QUESTION
      });
    });

    test('should handle appropriate questions with appropriate responses', async () => {
      // Mock content filtering to pass
      mockOpenAI.moderations.create.mockResolvedValueOnce({
        results: [{ flagged: false }]
      });

      // Mock OpenAI chat response
      const mockChatResponse = {
        choices: [{
          message: {
            content: 'AI is artificial intelligence'
          }
        }]
      };
      mockOpenAI.chat.completions.create.mockResolvedValueOnce(mockChatResponse);

      // Mock second content filtering for response
      mockOpenAI.moderations.create.mockResolvedValueOnce({
        results: [{ flagged: false }]
      });

      const response = await processPostRequest(mockEvent);
      expect(response.statusCode).toBe(200);
      expect(JSON.parse(response.body)).toEqual({
        answers: 'AI is artificial intelligence'
      });

      // Verify OpenAI chat was called with correct parameters
      expect(mockOpenAI.chat.completions.create).toHaveBeenCalledWith({
        model: expect.any(String),
        messages: expect.arrayContaining([...MESSAGES, {
          role: 'user',
          content: 'What is AI?'
        }]),
        max_tokens: 100,
        stop: ['user', ' assistant'],
        temperature: 0.2
      });
    });

    test('should handle appropriate questions with inappropriate responses', async () => {
      // Mock initial content filtering to pass
      mockOpenAI.moderations.create.mockResolvedValueOnce({
        results: [{ flagged: false }]
      });

      // Mock OpenAI chat response
      const mockChatResponse = {
        choices: [{
          message: {
            content: 'inappropriate response'
          }
        }]
      };
      mockOpenAI.chat.completions.create.mockResolvedValueOnce(mockChatResponse);

      // Mock response content filtering to fail
      mockOpenAI.moderations.create.mockResolvedValueOnce({
        results: [{ flagged: true }]
      });

      const response = await processPostRequest(mockEvent);
      expect(response.statusCode).toBe(200);
      expect(JSON.parse(response.body)).toEqual({
        answers: INAPPROPRIATE_CONTENT
      });
    });
  });

  describe('lambdaHandler', () => {
    const mockEvent = {
      httpMethod: 'POST',
      body: {
        question: 'What is AI?',
        max_tokens: 100
      }
    };
    const mockContext = {};

    test('should handle POST requests', async () => {
      // Mock router functions
      mockRouter.path_router.mockReturnValueOnce({
        POST: processPostRequest
      });
      mockRouter.route.mockImplementationOnce(
        (event, context, successMethod, _, unsupportedMethod, defaultRoute) => {
          return defaultRoute.POST(event, context);
        }
      );

      // Mock content filtering and chat response
      mockOpenAI.moderations.create.mockResolvedValueOnce({
        results: [{ flagged: false }]
      });
      mockOpenAI.chat.completions.create.mockResolvedValueOnce({
        choices: [{
          message: {
            content: 'AI is artificial intelligence'
          }
        }]
      });
      mockOpenAI.moderations.create.mockResolvedValueOnce({
        results: [{ flagged: false }]
      });

      const response = await lambdaHandler(mockEvent, mockContext);
      
      expect(mockRequestUtils.prepare_process_event).toHaveBeenCalledWith(
        mockEvent,
        mockContext,
        'NLP Chatbot students',
        null
      );
      expect(response.statusCode).toBe(200);
      expect(JSON.parse(response.body)).toEqual({
        answers: 'AI is artificial intelligence'
      });
    });
  });
});

// Helper functions that would be imported in the real implementation
async function filterContent(content) {
  const response = await mockOpenAI.moderations.create({ input: content });
  return response.results[0].flagged;
}

async function processPostRequest(event) {
  const params = event.body;
  const question = params.question;
  const max_tokens = params.max_tokens;

  // Check for harmful content
  const check_question = await filterContent(question);

  if (check_question) {
    return mockResponseUtils.success_response({ answers: INAPPROPRIATE_QUESTION });
  }

  // Define the prompt
  const messages = [...MESSAGES, {
    role: 'user',
    content: question
  }];

  const response = await mockOpenAI.chat.completions.create({
    model: 'gpt-3.5-turbo',
    messages,
    max_tokens,
    stop: ['user', ' assistant'],
    temperature: 0.2,
  });

  const llm_response = response.choices[0].message.content;

  // Filter the response
  const check_answer = await filterContent(llm_response);

  if (check_answer) {
    return mockResponseUtils.success_response({ answers: INAPPROPRIATE_CONTENT });
  }

  return mockResponseUtils.success_response({ answers: llm_response });
}

async function lambdaHandler(event, context) {
  mockRequestUtils.prepare_process_event(event, context, 'NLP Chatbot students', null);

  const defaultRoute = mockRouter.path_router('', {
    POST: processPostRequest
  });

  return mockRouter.route(
    event,
    context,
    mockResponseUtils.success_method,
    null,
    mockResponseUtils.unsupported_method,
    defaultRoute
  );
}
