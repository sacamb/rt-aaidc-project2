# Destination Compass Test Suite

Comprehensive test suite for the Destination Compass application.

## Test Structure

```
tests/
├── unit/                    # Unit tests for individual services
│   ├── test_geocoding_service.py
│   ├── test_weather_service.py
│   ├── test_news_service.py
│   ├── test_events_service.py
│   ├── test_time_service.py
│   └── test_llm_service.py
├── integration/            # Integration tests
│   ├── test_workflow.py    # Full workflow tests
│   └── test_edge_cases.py  # Edge case and error scenarios
├── fixtures/               # Test fixtures
├── conftest.py            # Shared pytest fixtures
└── run_tests.py           # Test runner script
```

## Running Tests

### Run All Tests

```bash
pytest
# or
python -m pytest
# or
python tests/run_tests.py
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_geocoding_service.py

# Specific test
pytest tests/unit/test_geocoding_service.py::TestGeocodingService::test_geocode_success
```

### Run with Coverage

```bash
pytest --cov=src --cov-report=html
```

Coverage report will be generated in `htmlcov/index.html`

### Run with Verbose Output

```bash
pytest -v
```

## Test Categories

### Unit Tests

Test individual services in isolation with mocked dependencies:

- **GeocodingService**: Location resolution and coordinate extraction
- **WeatherService**: Weather data retrieval and formatting
- **NewsService**: News headline fetching and filtering
- **EventsService**: Event search and parsing
- **TimeService**: Local time retrieval
- **LLMService**: Location extraction, intent classification, and report generation

### Integration Tests

Test the complete LangGraph workflow:

- **Full Workflow**: End-to-end destination query processing
- **Non-Destination Queries**: Intent classification and short-circuiting
- **API Failures**: Resilience to external API errors
- **Edge Cases**: Empty queries, special characters, timeouts, malformed responses

## Mocking Strategy

All external API calls are mocked using `unittest.mock`:

- **HTTP Requests**: `requests.get` and `requests.post` are mocked
- **LLM Calls**: `ChatGroq` and `ChatPromptTemplate` are mocked
- **Configuration**: `config_loader.config` is mocked with test values

## Test Fixtures

Shared fixtures in `conftest.py`:

- `mock_config`: Mock configuration loader
- `mock_env_vars`: Mock environment variables
- `sample_location_data`: Sample location structure
- `sample_weather_data`: Sample weather data
- `sample_news_data`: Sample news headlines
- `sample_events_data`: Sample events data
- `mock_requests_get/post`: Mock HTTP requests
- `mock_llm_response`: Mock LLM responses
- `sample_state`: Sample workflow state

## Writing New Tests

### Unit Test Example

```python
def test_service_method(self, mock_config):
    """Test description."""
    with patch('services.service_name.config', mock_config):
        service = ServiceName()
        
        # Mock external dependencies
        with patch('services.service_name.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {...}
            
            result = service.method_name(...)
            
            assert result == expected_value
```

### Integration Test Example

```python
def test_workflow_scenario(self, mock_all_services, mock_env_vars):
    """Test workflow scenario."""
    with patch('dotenv.load_dotenv'):
        app = DestinationCompassApp()
        
        initial_state = {...}
        result = app.graph.invoke(initial_state, config=app.execution_config)
        
        assert result.get("final_output") is not None
```

## Continuous Integration

Tests are designed to run in CI/CD pipelines:

- All external dependencies are mocked
- No actual API keys required
- Fast execution (< 30 seconds for full suite)
- Deterministic results

## Coverage Goals

- **Unit Tests**: > 90% coverage for all services
- **Integration Tests**: Cover all workflow paths
- **Edge Cases**: Test error scenarios and boundary conditions
