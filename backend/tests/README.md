# WingMan Backend Test Suite

Comprehensive test suite for the WingMan backend, covering unit tests, integration tests, and mock-based tests.

## Test Coverage

### 1. Unit Tests for Helper Functions

#### `build_system_prompt()`
- Tests prompt generation with full user profile
- Tests prompt generation without user profile
- Validates key instruction sections are included
- Tests with empty goals and special characters

#### `detect_dtmf()`
- Tests DTMF detection with various keywords (press, dial, enter)
- Tests digit and word-based DTMF (e.g., "press 1" vs "press one")
- Tests special characters (star, pound)
- Tests case insensitivity
- Tests edge cases with multiple spaces and punctuation

#### `pcm16_to_mulaw()`
- Tests basic PCM16 to mu-law audio conversion
- Tests with empty input, silence, and maximum amplitude
- Validates output length correctness

### 2. Integration Tests

#### `/twilio/voice/{call_id}` Webhook Endpoint
- Tests TwiML response generation
- Validates XML structure and WebSocket URL format
- Tests protocol conversion (HTTP→WS, HTTPS→WSS)
- Tests with various call IDs

### 3. Mock-Based Tests

#### `send_whatsapp_summary()`
- Tests successful WhatsApp summary sending with mocks
- Tests with and without user profile
- Tests empty transcript handling (early return)
- Tests Groq API error fallback
- Tests Twilio error handling
- Validates prompt construction and API calls

### 4. Storage Module Tests

Tests for all storage functions:
- `create_call()` - Creating call records
- `get_call()` - Retrieving calls
- `get_all_calls()` - Listing all calls
- `update_call_status()` - Status updates
- `set_twilio_sid()` - Setting Twilio SID
- `add_transcript_turn()` - Adding transcript entries
- `finalize_call()` - Finalizing calls
- `save_coach_report()` - Saving coach reports
- `save_profile()` / `get_profile()` - User profile management

## Running the Tests

### Prerequisites

Install test dependencies:

```bash
cd wingman
pip install pytest pytest-asyncio pytest-mock httpx
```

### Run All Tests

```bash
# From the wingman directory
pytest

# Or with more verbose output
pytest -v

# Or from the backend directory
cd backend
pytest tests/
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only mock-based tests
pytest -m mock

# Run only storage tests
pytest -m storage
```

### Run Specific Test Files

```bash
pytest backend/tests/test_twilio_handler.py
```

### Run Specific Test Classes or Functions

```bash
# Run a specific test class
pytest backend/tests/test_twilio_handler.py::TestBuildSystemPrompt

# Run a specific test function
pytest backend/tests/test_twilio_handler.py::TestBuildSystemPrompt::test_build_system_prompt_with_full_profile
```

### Run with Coverage

```bash
# Install coverage tool
pip install pytest-cov

# Run with coverage report
pytest --cov=backend --cov-report=html --cov-report=term

# View HTML coverage report
open htmlcov/index.html
```

## Test Structure

```
backend/tests/
├── __init__.py                    # Package marker
├── conftest.py                    # Shared fixtures and configuration
├── test_twilio_handler.py         # Main test suite
└── README.md                      # This file
```

## Key Fixtures

### `sample_user_profile`
Provides a sample UserProfile object for testing.

### `sample_call_brief`
Provides a sample CallBrief object for testing.

### `sample_transcript`
Provides a sample conversation transcript for testing.

### `test_app` and `client`
Provides a FastAPI test application and client for integration tests.

### `reset_storage`
Automatically resets storage state before each test (autouse fixture).

## Writing New Tests

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Example Test

```python
def test_my_function():
    """Test description."""
    # Arrange
    input_data = "test"
    
    # Act
    result = my_function(input_data)
    
    # Assert
    assert result == expected_output
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await async_function()
    assert result is not None
```

### Using Mocks

```python
from unittest.mock import patch, Mock

def test_with_mock():
    """Test with mocked dependency."""
    with patch('module.dependency') as mock_dep:
        mock_dep.return_value = "mocked"
        result = function_using_dependency()
        assert result == "expected"
        mock_dep.assert_called_once()
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines. Ensure all tests pass before merging code.

## Troubleshooting

### Import Errors

If you encounter import errors, ensure you're running pytest from the `wingman` directory:

```bash
cd wingman
pytest
```

### Async Test Warnings

If you see warnings about async tests, ensure `pytest-asyncio` is installed:

```bash
pip install pytest-asyncio
```

### Mock Not Working

Ensure you're patching the correct import path. Use the path where the function is used, not where it's defined:

```python
# If twilio_handler.py imports: from twilio.rest import Client
# Patch it as:
with patch('backend.twilio_handler.Client'):
    # test code
```

## Test Metrics

- **Total Tests**: 60+
- **Unit Tests**: 25+
- **Integration Tests**: 5+
- **Mock Tests**: 10+
- **Storage Tests**: 20+

## Contributing

When adding new features:

1. Write tests first (TDD approach recommended)
2. Ensure all existing tests pass
3. Add tests for edge cases
4. Update this README if adding new test categories

## License

Same as the main WingMan project.