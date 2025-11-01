"""
Unit tests for Llave MX OAuth2 Backend

Tests cover:
- Response validation
- User data mapping
- PKCE generation
- Token exchange
- Error handling
"""
import json
import os
import unittest
from unittest.mock import Mock, patch, MagicMock

# Import the backend
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from oauth2_llavemx.llavemx_oauth import LlaveMXOAuth2


class TestLlaveMXValidation(unittest.TestCase):
    """Test validation methods"""
    
    def setUp(self):
        """Load test fixtures"""
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        
    def load_fixture(self, filename):
        """Load JSON fixture file"""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def test_load_fixtures(self):
        """Verify all fixtures load correctly"""
        fixtures = [
            'llavemx-token-ok.json',
            'llavemx-token-invalid.json',
            'llavemx-user-ok-nacional.json',
            'llavemx-user-ok-extranjero.json',
            'llavemx-user-invalid-token.json',
            'llavemx-roles-ok.json',
            'llavemx-logout-ok.json',
        ]
        
        for fixture in fixtures:
            data = self.load_fixture(fixture)
            self.assertIsInstance(data, dict, f"Fixture {fixture} should be a dict")
    
    def test_is_valid_dict(self):
        """Test generic dict validation"""
        backend = LlaveMXOAuth2()
        
        # Valid dict
        valid_dict = {"key1": "value1", "key2": "value2"}
        self.assertTrue(backend.is_valid_dict(valid_dict, ["key1", "key2"]))
        
        # Missing key
        self.assertFalse(backend.is_valid_dict(valid_dict, ["key1", "key3"]))
        
        # Not a dict
        self.assertFalse(backend.is_valid_dict("not a dict", ["key1"]))
        self.assertFalse(backend.is_valid_dict(None, ["key1"]))
    
    def test_is_valid_llavemx_response(self):
        """Test Llave MX user response validation"""
        backend = LlaveMXOAuth2()
        
        # Valid response
        user_data = self.load_fixture('llavemx-user-ok-nacional.json')
        self.assertTrue(backend.is_valid_llavemx_response(user_data))
        
        # Invalid response (missing required fields)
        invalid_data = {"id": "123"}
        self.assertFalse(backend.is_valid_llavemx_response(invalid_data))
    
    def test_is_llavemx_error(self):
        """Test error response detection"""
        backend = LlaveMXOAuth2()
        
        # Valid error response
        error_data = self.load_fixture('llavemx-token-invalid.json')
        self.assertTrue(backend.is_llavemx_error(error_data))
        
        # Not an error
        user_data = self.load_fixture('llavemx-user-ok-nacional.json')
        self.assertFalse(backend.is_llavemx_error(user_data))
    
    def test_is_token_response(self):
        """Test token response validation"""
        backend = LlaveMXOAuth2()
        
        # Valid token response
        token_data = self.load_fixture('llavemx-token-ok.json')
        self.assertTrue(backend.is_token_response(token_data))
        
        # Invalid token response
        invalid_token = {"error": "invalid_grant"}
        self.assertFalse(backend.is_token_response(invalid_token))


class TestLlaveMXUserMapping(unittest.TestCase):
    """Test user data mapping"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.backend = LlaveMXOAuth2()
    
    def load_fixture(self, filename):
        """Load JSON fixture"""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def test_get_user_details_nacional(self):
        """Test user mapping for national user with full data"""
        user_response = self.load_fixture('llavemx-user-ok-nacional.json')
        user_details = self.backend.get_user_details(user_response)
        
        # Check required fields
        self.assertEqual(user_details['username'], 'PEGG900115HDFRZN09')
        self.assertEqual(user_details['email'], 'juan.perez@educacion.gob.mx')
        self.assertEqual(user_details['first_name'], 'Juan')
        self.assertEqual(user_details['last_name'], 'Pérez García')
        self.assertEqual(user_details['curp'], 'PEGG900115HDFRZN09')
        
        # Check additional fields
        self.assertEqual(user_details['telefono'], '5512345678')
        self.assertEqual(user_details['fechaNacimiento'], '1990-01-15')
        self.assertEqual(user_details['sexo'], 'H')
        self.assertTrue(user_details['correoVerificado'])
        self.assertTrue(user_details['telefonoVerificado'])
    
    def test_get_user_details_sin_segundo_apellido(self):
        """Test user mapping when segundoApellido is missing"""
        user_response = self.load_fixture('llavemx-user-ok-extranjero.json')
        user_details = self.backend.get_user_details(user_response)
        
        # Last name should only contain primerApellido
        self.assertEqual(user_details['last_name'], 'González')
        self.assertEqual(user_details['username'], 'ROGE750310HNEXXX01')
    
    def test_get_user_details_sin_verificar(self):
        """Test user with unverified phone"""
        user_response = self.load_fixture('llavemx-user-ok-sin-verificar.json')
        user_details = self.backend.get_user_details(user_response)
        
        # Email verified but not phone
        self.assertTrue(user_details['correoVerificado'])
        self.assertFalse(user_details['telefonoVerificado'])
        self.assertEqual(user_details['first_name'], 'María')
        self.assertEqual(user_details['last_name'], 'López Martínez')
    
    def test_get_user_details_campos_vacios(self):
        """Test handling of empty/missing fields"""
        minimal_response = {
            "id": "999",
            "correo": "test@example.com",
            "nombre": "Test",
            "primerApellido": "User",
            "segundoApellido": "",
            "login": "TEST000000HDFXXX00"
        }
        
        user_details = self.backend.get_user_details(minimal_response)
        
        # Should handle missing fields gracefully
        self.assertEqual(user_details['username'], 'TEST000000HDFXXX00')
        self.assertEqual(user_details['telefono'], '')
        self.assertEqual(user_details['fechaNacimiento'], '')
        self.assertFalse(user_details['correoVerificado'])


class TestLlaveMXPKCE(unittest.TestCase):
    """Test PKCE implementation"""
    
    def setUp(self):
        """Setup backend instance"""
        self.backend = LlaveMXOAuth2()
    
    def test_generate_code_verifier(self):
        """Test code verifier generation"""
        verifier = self.backend.generate_code_verifier()
        
        # Should be a string
        self.assertIsInstance(verifier, str)
        
        # Should be 43-128 characters (RFC 7636)
        self.assertGreaterEqual(len(verifier), 43)
        self.assertLessEqual(len(verifier), 128)
        
        # Should be URL-safe
        import string
        allowed_chars = string.ascii_letters + string.digits + '-_'
        self.assertTrue(all(c in allowed_chars for c in verifier))
    
    def test_generate_code_challenge(self):
        """Test code challenge generation from verifier"""
        verifier = "test_verifier_1234567890abcdefghijklmnop"
        challenge = self.backend.generate_code_challenge(verifier)
        
        # Should be a string
        self.assertIsInstance(challenge, str)
        
        # Should be base64url encoded (43 characters for SHA256)
        self.assertEqual(len(challenge), 43)
        
        # Should be deterministic (same input = same output)
        challenge2 = self.backend.generate_code_challenge(verifier)
        self.assertEqual(challenge, challenge2)
    
    def test_code_verifier_persistence(self):
        """Test that code verifier is stored and retrievable"""
        verifier1 = self.backend.generate_code_verifier()
        verifier2 = self.backend.generate_code_verifier()
        
        # Should return same verifier (cached)
        self.assertEqual(verifier1, verifier2)


class TestLlaveMXAuthParams(unittest.TestCase):
    """Test authentication parameter generation"""
    
    def setUp(self):
        """Setup backend with mocked strategy"""
        self.backend = LlaveMXOAuth2()
        
        # Mock strategy for session management
        self.backend.strategy = Mock()
        self.backend.strategy.session_set = Mock()
        self.backend.strategy.session_get = Mock(return_value=None)
        
        # Mock settings
        self.backend.setting = Mock(return_value='test_client_id')
    
    def test_auth_params_includes_pkce(self):
        """Test that authorization params include PKCE parameters"""
        # Mock parent method
        with patch.object(LlaveMXOAuth2.__bases__[0], 'auth_params', return_value={}):
            params = self.backend.auth_params(state='test_state')
        
        # Should include PKCE parameters
        self.assertIn('code_challenge', params)
        self.assertIn('code_challenge_method', params)
        self.assertEqual(params['code_challenge_method'], 'S256')
        
        # Should store verifier in session
        self.backend.strategy.session_set.assert_called_once()
        call_args = self.backend.strategy.session_set.call_args
        self.assertEqual(call_args[0][0], 'code_verifier')


class TestLlaveMXEndpoints(unittest.TestCase):
    """Test endpoint configuration"""
    
    def test_endpoints_are_set(self):
        """Verify all required endpoints are configured"""
        backend = LlaveMXOAuth2()
        
        # Check authorization endpoint
        self.assertEqual(
            backend.AUTHORIZATION_URL,
            "https://val-llave.infotec.mx/oauth.xhtml"
        )
        
        # Check token endpoint
        self.assertEqual(
            backend.ACCESS_TOKEN_URL,
            "https://val-api-llave.infotec.mx/ws/rest/apps/oauth/obtenerToken"
        )
        
        # Check user data endpoint
        self.assertEqual(
            backend.USER_DATA_URL,
            "https://val-api-llave.infotec.mx/ws/rest/apps/oauth/datosUsuario"
        )
        
        # Check roles endpoint
        self.assertEqual(
            backend.ROLES_URL,
            "https://val-api-llave.infotec.mx/ws/rest/apps/oauth/getRolesUsuarioLogueado"
        )
        
        # Check logout endpoint
        self.assertEqual(
            backend.LOGOUT_URL,
            "https://val-api-llave.infotec.mx/ws/rest/apps/auth/cerrarSesion"
        )
    
    def test_backend_name(self):
        """Test backend identifier"""
        backend = LlaveMXOAuth2()
        self.assertEqual(backend.name, "llavemx")
    
    def test_pkce_enabled(self):
        """Test PKCE is enabled"""
        backend = LlaveMXOAuth2()
        self.assertTrue(backend.OAUTH_PKCE_ENABLED)


class TestLlaveMXRoles(unittest.TestCase):
    """Test role management (optional feature)"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.backend = LlaveMXOAuth2()
        self.backend.setting = Mock(return_value='test_client_id')
    
    def load_fixture(self, filename):
        """Load JSON fixture"""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def test_roles_response_structure(self):
        """Test roles response has expected structure"""
        roles_data = self.load_fixture('llavemx-roles-ok.json')
        
        self.assertIn('roles', roles_data)
        self.assertIsInstance(roles_data['roles'], list)
        self.assertEqual(len(roles_data['roles']), 2)
        
        # Check first role structure
        role = roles_data['roles'][0]
        self.assertIn('id', role)
        self.assertIn('nombre', role)
        self.assertIn('descripcion', role)


class TestLlaveMXLogout(unittest.TestCase):
    """Test logout functionality"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
    
    def load_fixture(self, filename):
        """Load JSON fixture"""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def test_logout_response_structure(self):
        """Test logout success response"""
        logout_data = self.load_fixture('llavemx-logout-ok.json')
        
        self.assertEqual(logout_data['codeResponse'], 101)
        self.assertEqual(logout_data['mensaje'], 'Logout success')


class TestLlaveMXErrors(unittest.TestCase):
    """Test error handling"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
    
    def load_fixture(self, filename):
        """Load JSON fixture"""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def test_token_invalid_grant_error(self):
        """Test invalid_grant error (expired code)"""
        error_data = self.load_fixture('llavemx-token-invalid.json')
        
        self.assertEqual(error_data['error'], 'invalid_grant')
        self.assertIn('expirado', error_data['error_description'].lower())
    
    def test_token_invalid_client_error(self):
        """Test invalid_client error"""
        error_data = self.load_fixture('llavemx-token-invalid-client.json')
        
        self.assertEqual(error_data['error'], 'invalid_client')
        self.assertIn('clientid', error_data['error_description'].lower())
    
    def test_user_invalid_token_error(self):
        """Test invalid_token error (expired access token)"""
        error_data = self.load_fixture('llavemx-user-invalid-token.json')
        
        self.assertEqual(error_data['error'], 'invalid_token')


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestLlaveMXValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestLlaveMXUserMapping))
    suite.addTests(loader.loadTestsFromTestCase(TestLlaveMXPKCE))
    suite.addTests(loader.loadTestsFromTestCase(TestLlaveMXAuthParams))
    suite.addTests(loader.loadTestsFromTestCase(TestLlaveMXEndpoints))
    suite.addTests(loader.loadTestsFromTestCase(TestLlaveMXRoles))
    suite.addTests(loader.loadTestsFromTestCase(TestLlaveMXLogout))
    suite.addTests(loader.loadTestsFromTestCase(TestLlaveMXErrors))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    exit(run_tests())
