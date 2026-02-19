"""Tests for utils module."""
import unittest
from utils.validators import validate_symbol, validate_order_params
from utils.cache import DataCache
from utils.decorators import retry_with_backoff


class TestValidators(unittest.TestCase):
    """Test validators."""
    
    def test_validate_symbol_valid(self):
        """Test valid symbol."""
        self.assertTrue(validate_symbol("NIFTY"))
    
    def test_validate_symbol_empty(self):
        """Test empty symbol."""
        with self.assertRaises(ValueError):
            validate_symbol("")
    
    def test_validate_symbol_lowercase(self):
        """Test lowercase symbol."""
        with self.assertRaises(ValueError):
            validate_symbol("nifty")
    
    def test_validate_order_params_valid(self):
        """Test valid order params."""
        self.assertTrue(validate_order_params("NIFTY", 100, 18000.0))
    
    def test_validate_order_params_invalid_quantity(self):
        """Test invalid quantity."""
        with self.assertRaises(ValueError):
            validate_order_params("NIFTY", -1, 18000.0)


class TestDataCache(unittest.TestCase):
    """Test data cache."""
    
    def test_cache_get_set(self):
        """Test cache get/set."""
        cache = DataCache(ttl_minutes=5)
        cache.set("key", "value")
        self.assertEqual(cache.get("key"), "value")
    