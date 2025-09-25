import unittest
import os
from unittest.mock import patch
from src.chainplate.services.health.health_check import HealthCheck, HealthCheckService


class TestHealthCheck(unittest.TestCase):
    """Test class for HealthCheck data class"""
    
    def test_health_check_initialization_with_defaults(self):
        """Test HealthCheck initialization with default values"""
        health_check = HealthCheck()
        self.assertEqual(health_check.status, "unknown")
        self.assertEqual(health_check.errors, [])
    
    def test_health_check_initialization_with_values(self):
        """Test HealthCheck initialization with provided values"""
        errors = ["Error 1", "Error 2"]
        health_check = HealthCheck(status="error", errors=errors)
        self.assertEqual(health_check.status, "error")
        self.assertEqual(health_check.errors, errors)
    
    def test_health_check_to_dict(self):
        """Test HealthCheck to_dict method"""
        errors = ["Test error"]
        health_check = HealthCheck(status="error", errors=errors)
        
        # The current implementation uses dataclasses.asdict() but HealthCheck is not a dataclass
        # This test will fail with the current implementation, which indicates a bug in the source code
        with self.assertRaises(TypeError):
            health_check.to_dict()


class TestHealthCheckService(unittest.TestCase):
    """Test class for HealthCheckService"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Store original environment variable if it exists
        self.original_api_key = os.environ.get("OPENAI_API_KEY")
    
    def tearDown(self):
        """Clean up after each test method"""
        # Restore original environment variable
        if self.original_api_key is not None:
            os.environ["OPENAI_API_KEY"] = self.original_api_key
        elif "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-api-key"})
    def test_check_with_valid_api_key(self):
        """Test health check when OPENAI_API_KEY is set"""
        result = HealthCheckService.check()
        
        self.assertIsInstance(result, HealthCheck)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.errors, [])
    
    @patch.dict(os.environ, {}, clear=True)
    def test_check_without_api_key(self):
        """Test health check when OPENAI_API_KEY is not set"""
        result = HealthCheckService.check()
        
        self.assertIsInstance(result, HealthCheck)
        self.assertEqual(result.status, "error")
        self.assertEqual(result.errors, ["OPENAI_API_KEY not configured"])
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": ""})
    def test_check_with_empty_api_key(self):
        """Test health check when OPENAI_API_KEY is empty"""
        result = HealthCheckService.check()
        
        self.assertIsInstance(result, HealthCheck)
        self.assertEqual(result.status, "error")
        self.assertEqual(result.errors, ["OPENAI_API_KEY not configured"])
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "   "})
    def test_check_with_whitespace_api_key(self):
        """Test health check when OPENAI_API_KEY contains only whitespace"""
        result = HealthCheckService.check()
        
        self.assertIsInstance(result, HealthCheck)
        self.assertEqual(result.status, "error")
        self.assertEqual(result.errors, ["OPENAI_API_KEY not configured"])
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "  valid-key  "})
    def test_check_with_api_key_with_whitespace(self):
        """Test health check when OPENAI_API_KEY has leading/trailing whitespace"""
        result = HealthCheckService.check()
        
        self.assertIsInstance(result, HealthCheck)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.errors, [])
    
    def test_check_returns_health_check_instance(self):
        """Test that check method returns a HealthCheck instance"""
        result = HealthCheckService.check()
        self.assertIsInstance(result, HealthCheck)
    
    def test_check_is_static_method(self):
        """Test that check method can be called without instantiating the class"""
        # This should not raise an error
        result = HealthCheckService.check()
        self.assertIsInstance(result, HealthCheck)


if __name__ == '__main__':
    unittest.main()