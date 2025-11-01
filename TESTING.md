# Testing Instructions for Llave MX OAuth2 Backend

## Setup

### 1. Install Development Dependencies

```bash
cd /Users/diegonicolas/Desktop/oauth/Edx-Oauth2

# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install package in development mode
pip install -e .

# Install test dependencies
pip install pytest pytest-cov mock
```

### 2. Verify Installation

```bash
python -c "from oauth2_llavemx.llavemx_oauth import LlaveMXOAuth2; print('✓ Import successful')"
```

## Running Tests

### Option 1: Run with Python unittest

```bash
# Run all tests
python tests/test_llavemx.py

# With verbose output
python tests/test_llavemx.py -v
```

### Option 2: Run with pytest (recommended)

```bash
# Run all Llave MX tests
pytest tests/test_llavemx.py -v

# Run with coverage report
pytest tests/test_llavemx.py --cov=oauth2_llavemx --cov-report=html

# Run specific test class
pytest tests/test_llavemx.py::TestLlaveMXValidation -v

# Run specific test method
pytest tests/test_llavemx.py::TestLlaveMXValidation::test_is_valid_llavemx_response -v
```

### Option 3: Run old NEM tests (for compatibility)

```bash
python tests/tests.py
```

## Expected Output

### Success Output

```
test_auth_params_includes_pkce (__main__.TestLlaveMXAuthParams) ... ok
test_backend_name (__main__.TestLlaveMXEndpoints) ... ok
test_endpoints_are_set (__main__.TestLlaveMXEndpoints) ... ok
test_pkce_enabled (__main__.TestLlaveMXEndpoints) ... ok
test_token_invalid_client_error (__main__.TestLlaveMXErrors) ... ok
test_token_invalid_grant_error (__main__.TestLlaveMXErrors) ... ok
test_user_invalid_token_error (__main__.TestLlaveMXErrors) ... ok
test_logout_response_structure (__main__.TestLlaveMXLogout) ... ok
test_code_challenge (__main__.TestLlaveMXPKCE) ... ok
test_code_verifier (__main__.TestLlaveMXPKCE) ... ok
test_code_verifier_persistence (__main__.TestLlaveMXPKCE) ... ok
test_roles_response_structure (__main__.TestLlaveMXRoles) ... ok
test_get_user_details_campos_vacios (__main__.TestLlaveMXUserMapping) ... ok
test_get_user_details_nacional (__main__.TestLlaveMXUserMapping) ... ok
test_get_user_details_sin_segundo_apellido (__main__.TestLlaveMXUserMapping) ... ok
test_get_user_details_sin_verificar (__main__.TestLlaveMXUserMapping) ... ok
test_is_llavemx_error (__main__.TestLlaveMXValidation) ... ok
test_is_token_response (__main__.TestLlaveMXValidation) ... ok
test_is_valid_dict (__main__.TestLlaveMXValidation) ... ok
test_is_valid_llavemx_response (__main__.TestLlaveMXValidation) ... ok
test_load_fixtures (__main__.TestLlaveMXValidation) ... ok

----------------------------------------------------------------------
Ran 21 tests in 0.045s

OK
```

## Test Coverage

The test suite covers:

✅ **Validation Methods** (5 tests)
- Dictionary validation
- Response structure validation
- Error detection
- Token response validation

✅ **User Data Mapping** (4 tests)
- National user with full data
- User without segundo apellido
- User with unverified phone
- Handling of empty/missing fields

✅ **PKCE Implementation** (3 tests)
- Code verifier generation
- Code challenge calculation
- Verifier persistence

✅ **Authentication Parameters** (1 test)
- PKCE parameters in auth request

✅ **Endpoint Configuration** (3 tests)
- Correct endpoint URLs
- Backend identifier
- PKCE enabled flag

✅ **Role Management** (1 test)
- Roles response structure

✅ **Logout** (1 test)
- Logout response validation

✅ **Error Handling** (3 tests)
- Invalid grant error
- Invalid client error
- Invalid token error

## Manual Testing with Fixtures

### Test User Data Mapping

```python
import json
from oauth2_llavemx.llavemx_oauth import LlaveMXOAuth2

backend = LlaveMXOAuth2()

# Load fixture
with open('tests/data/llavemx-user-ok-nacional.json', 'r') as f:
    user_data = json.load(f)

# Test mapping
user_details = backend.get_user_details(user_data)
print(json.dumps(user_details, indent=2))
```

### Test PKCE Generation

```python
from oauth2_llavemx.llavemx_oauth import LlaveMXOAuth2

backend = LlaveMXOAuth2()

# Generate verifier
verifier = backend.generate_code_verifier()
print(f"Verifier: {verifier}")
print(f"Length: {len(verifier)}")

# Generate challenge
challenge = backend.generate_code_challenge(verifier)
print(f"Challenge: {challenge}")
print(f"Length: {len(challenge)}")
```

### Test Validation Methods

```python
import json
from oauth2_llavemx.llavemx_oauth import LlaveMXOAuth2

backend = LlaveMXOAuth2()

# Test error detection
with open('tests/data/llavemx-token-invalid.json', 'r') as f:
    error_data = json.load(f)

is_error = backend.is_llavemx_error(error_data)
print(f"Is error: {is_error}")  # Should be True

# Test valid response
with open('tests/data/llavemx-user-ok-nacional.json', 'r') as f:
    user_data = json.load(f)

is_valid = backend.is_valid_llavemx_response(user_data)
print(f"Is valid: {is_valid}")  # Should be True
```

## Integration Testing (with Mocks)

Since we can't test against the real Llave MX API without credentials, tests use mocks:

```python
import unittest
from unittest.mock import Mock, patch
from oauth2_llavemx.llavemx_oauth import LlaveMXOAuth2

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.backend = LlaveMXOAuth2()
        self.backend.strategy = Mock()
        self.backend.setting = Mock(return_value='test_client_id')
    
    @patch('oauth2_llavemx.llavemx_oauth.urlopen')
    def test_user_data_retrieval(self, mock_urlopen):
        # Mock response
        mock_response = Mock()
        mock_response.read.return_value = json.dumps({
            "id": "123",
            "curp": "TEST000000HDFXXX00",
            "correo": "test@example.com",
            "nombre": "Test"
        }).encode('utf-8')
        mock_urlopen.return_value = mock_response
        
        # Test
        user_data = self.backend.user_data('fake_token')
        self.assertEqual(user_data['curp'], 'TEST000000HDFXXX00')
```

## Troubleshooting

### Import Errors

```bash
# If you get import errors
export PYTHONPATH="${PYTHONPATH}:/Users/diegonicolas/Desktop/oauth/Edx-Oauth2"
python tests/test_llavemx.py
```

### Fixture Not Found

```bash
# Make sure you're in the project root
cd /Users/diegonicolas/Desktop/oauth/Edx-Oauth2
python tests/test_llavemx.py
```

### Django Not Available

```bash
# If tests require Django models
pip install Django

# Or mock Django components
export DJANGO_SETTINGS_MODULE=test_settings
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.7, 3.8, 3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        pip install -e .
        pip install pytest pytest-cov
    - name: Run tests
      run: pytest tests/test_llavemx.py -v --cov=oauth2_llavemx
```

## Coverage Report

To generate HTML coverage report:

```bash
pytest tests/test_llavemx.py --cov=oauth2_llavemx --cov-report=html
open htmlcov/index.html  # On macOS
```

Target coverage: **>80%** for production readiness

## Next Steps

1. ✅ Run all tests locally
2. ✅ Verify 100% pass rate
3. ✅ Review coverage report
4. ⏭️ Test in development Open edX environment
5. ⏭️ Test with real Llave MX API (staging)
6. ⏭️ Perform load testing
7. ⏭️ Deploy to production

## Questions?

Open an issue: https://github.com/aprendemx/Edx-Oauth2/issues
