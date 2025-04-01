# LLM Lambda Functions Test Suite

This repository contains test cases for various Lambda functions in the LLM project.

## Project Structure
```
.
├── tests/
│   ├── __init__.py
│   ├── test_ask_ai.py
│   ├── dashboard.py
│   ├── dashboard.test.js
│   ├── launchTrain.test.js
│   ├── aiclubChatBot.test.js
│   └── askAi.test.js
├── requirements.txt
└── README.md
```

## Test Suites

The project includes test suites for the following Lambda functions:

1. **AskAI Lambda Tests**
   - Testing service ID functionality
   - Testing prediction ID handling
   - Testing timestamp filters
   - Testing monitor mode for super users
   - Error handling for missing parameters

2. **Launch Train Lambda Tests**
   - Testing model training initialization
   - Testing training parameters validation
   - Testing training status monitoring

3. **Dashboard Lambda Tests**
   - Testing data visualization endpoints
   - Testing metrics aggregation
   - Testing user-specific dashboard views

4. **AI Club ChatBot Lambda Tests**
   - Testing chat interactions
   - Testing response generation
   - Testing context handling

## Running Tests

### Python Tests
1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run Python tests:
```bash
pytest tests/*.py -v
```

### JavaScript Tests
1. Install Node dependencies:
```bash
npm install
```

2. Run JavaScript tests:
```bash
npm test
