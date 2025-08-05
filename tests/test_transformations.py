"""
Tests for the secure transformations module.

This module tests the new secure transformation system that replaces
the deprecated code execution functionality.
"""

import pytest
import tempfile
import os
import logging
from unittest.mock import Mock, patch
import numpy as np

from sovabids.transformations import (
    safe_string_concatenation,
    _get_nested_value,
    apply_safe_transformations,
    execute_safe_raw_functions,
    get_available_functions,
    get_function_documentation,
    RAW_FUNCTIONS,
    register_raw_function
)

class TestStringConcatenation:
    """Test the safe string concatenation functionality."""
    
    def test_simple_concatenation(self):
        """Test basic string concatenation with [variable] syntax."""
        variables = {
            'subject': '001',
            'session': 'ses1',
            'task': 'rest'
        }
        
        # Simple variable replacement
        result = safe_string_concatenation("[subject]", variables)
        assert result == "001"
        
        # Multiple variables with literal text (no + operator)
        result = safe_string_concatenation("[subject]_[session]", variables)
        assert result == "001_ses1"
        
        # Plus concatenation (splits on + and joins)
        result = safe_string_concatenation("[subject] + [session]", variables)
        assert result == "001ses1"
        
        # Plus concatenation with literal text
        result = safe_string_concatenation("sub + [subject]", variables)
        assert result == "sub001"
        
        # Multiple plus operations
        result = safe_string_concatenation("[subject] + _ + [session]", variables)
        assert result == "001_ses1"
    
    def test_nested_variable_access(self):
        """Test accessing nested dictionary values with dot notation."""
        variables = {
            'entities': {
                'subject': '001',
                'session': 'ses1',
                'task': 'rest'
            },
            'dataset_description': {
                'Name': 'MyStudy',
                'Version': 'v1.0'
            }
        }
        
        # Access nested values
        result = safe_string_concatenation("[entities.subject]", variables)
        assert result == "001"
        
        result = safe_string_concatenation("[entities.subject]_[entities.session]", variables)
        assert result == "001_ses1"
        
        result = safe_string_concatenation("[dataset_description.Name] + [dataset_description.Version]", variables)
        assert result == "MyStudyv1.0"
    
    def test_missing_variables(self):
        """Test behavior when variables are missing."""
        variables = {'existing': 'value'}
        
        # Missing variable should keep placeholder
        result = safe_string_concatenation("[missing]", variables)
        assert result == "[missing]"
        
        # Mixed existing and missing
        result = safe_string_concatenation("[existing]_[missing]", variables)
        assert result == "value_[missing]"
    
    def test_complex_expressions(self):
        """Test complex concatenation expressions."""
        variables = {
            'prefix': 'sub',
            'number': '001',
            'suffix': 'processed',
            'separator': '_'
        }
        
        # Multiple concatenations with + operator
        result = safe_string_concatenation("[prefix] + [number] + [suffix]", variables)
        assert result == "sub001processed"
        
        # Mixed literal and variable text with + operator
        result = safe_string_concatenation("processed + [prefix] + [number]", variables)
        assert result == "processedsub001"
        
        # Literal text without + operator (underscores preserved)
        result = safe_string_concatenation("processed_[prefix]_[number]", variables)
        assert result == "processed_sub_001"
        
        # Spaces around + are ignored
        result = safe_string_concatenation("[prefix]+[number]", variables)  # No spaces
        assert result == "sub001"
        
        result = safe_string_concatenation("[prefix]  +  [number]", variables)  # Extra spaces
        assert result == "sub001"
    
    def test_non_string_input(self):
        """Test handling of non-string input."""
        variables = {'num': 123}
        
        # Non-string expression should be converted to string
        result = safe_string_concatenation(123, variables)
        assert result == "123"
        
        # Non-string variables should be converted
        result = safe_string_concatenation("[num]", variables)
        assert result == "123"
    
    def test_empty_and_none_values(self):
        """Test handling of empty and None values."""
        variables = {
            'empty': '',
            'none_val': None,
            'valid': 'test'
        }
        
        result = safe_string_concatenation("[empty]", variables)
        assert result == ""
        
        result = safe_string_concatenation("[none_val]", variables)
        assert result == "None"
        
        result = safe_string_concatenation("[valid]_[empty]", variables)
        assert result == "test_"

class TestNestedValueAccess:
    """Test the nested value access utility function."""
    
    def test_simple_key_access(self):
        """Test simple dictionary key access."""
        data = {'key': 'value', 'number': 123}
        
        assert _get_nested_value(data, 'key') == 'value'
        assert _get_nested_value(data, 'number') == 123
        assert _get_nested_value(data, 'missing') is None
    
    def test_nested_key_access(self):
        """Test nested dictionary access with dot notation."""
        data = {
            'level1': {
                'level2': {
                    'key': 'deep_value'
                },
                'simple': 'value1'
            },
            'root': 'root_value'
        }
        
        assert _get_nested_value(data, 'level1.level2.key') == 'deep_value'
        assert _get_nested_value(data, 'level1.simple') == 'value1'
        assert _get_nested_value(data, 'root') == 'root_value'
        assert _get_nested_value(data, 'level1.missing') is None
        assert _get_nested_value(data, 'missing.level2') is None

class TestSafeTransformations:
    """Test the safe transformations application."""
    
    def test_apply_transformations(self):
        """Test applying multiple transformations."""
        operations = {
            'entities.subject': '[prefix] + [number]',
            'entities.session': '[type]_[id]',
            'simple': '[value]'
        }
        
        variables = {
            'prefix': 'sub',
            'number': '001',
            'type': 'rest',
            'id': '01',
            'value': 'test'
        }
        
        results = apply_safe_transformations(operations, variables)
        
        assert results['entities.subject'] == 'sub001'
        assert results['entities.session'] == 'rest_01'
        assert results['simple'] == 'test'
    
    def test_transformation_errors(self):
        """Test error handling in transformations."""
        operations = {
            'valid': '[existing]',
            'invalid': '[missing]'
        }
        
        variables = {'existing': 'value'}
        
        # Should not raise exception, should handle errors gracefully
        results = apply_safe_transformations(operations, variables)
        
        assert results['valid'] == 'value'
        assert results['invalid'] == '[missing]'  # Keeps placeholder

class TestRawFunctions:
    """Test the raw processing functions."""
    
    def setUp(self):
        """Set up mock raw object for testing."""
        self.mock_raw = Mock()
        self.mock_raw.info = {
            'sfreq': 1000,
            'nchan': 64,
            'bads': ['T7', 'T8']
        }
        self.mock_raw.ch_names = ['Fp1', 'Fp2', 'F3', 'F4', 'T7', 'T8']
        self.mock_raw.times = np.array([0, 1, 2, 3, 4, 5])
        
    def test_function_registry(self):
        """Test that built-in functions are properly registered."""
        available_functions = get_available_functions()
        
        # Check that expected functions are available
        expected_functions = [
            'print_info',
            'drop_bad_channels', 
            'set_montage_standard_1020',
            'filter_line_noise_50hz',
            'filter_line_noise_60hz',
            'resample_500hz',
            'crop_to_10min'
        ]
        
        for func_name in expected_functions:
            assert func_name in available_functions
    
    def test_function_documentation(self):
        """Test that functions have documentation."""
        docs = get_function_documentation()
        
        # All functions should have some documentation
        for func_name in get_available_functions():
            assert func_name in docs
            assert isinstance(docs[func_name], str)
            assert len(docs[func_name]) > 0
    
    def test_register_custom_function(self):
        """Test registering a custom function."""
        # Store original functions to restore later
        original_functions = RAW_FUNCTIONS.copy()
        
        try:
            @register_raw_function("test_function")
            def test_function(raw):
                """Test function documentation."""
                raw.test_attribute = "tested"
                return raw
            
            # Check function is registered
            assert "test_function" in RAW_FUNCTIONS
            assert RAW_FUNCTIONS["test_function"] == test_function
            
            # Check it appears in available functions
            assert "test_function" in get_available_functions()
            
            # Check documentation
            docs = get_function_documentation()
            assert "test_function" in docs
            assert "Test function documentation." in docs["test_function"]
            
        finally:
            # Restore original functions
            RAW_FUNCTIONS.clear()
            RAW_FUNCTIONS.update(original_functions)
    
    def test_execute_safe_functions(self):
        """Test executing safe raw functions."""
        self.setUp()
        
        # Mock the specific functions we want to test
        with patch.dict(RAW_FUNCTIONS, {
            'test_func1': Mock(return_value=self.mock_raw),
            'test_func2': Mock(return_value=self.mock_raw)
        }):
            
            function_names = ['test_func1', 'test_func2']
            result = execute_safe_raw_functions(function_names, self.mock_raw)
            
            # Check functions were called
            RAW_FUNCTIONS['test_func1'].assert_called_once_with(self.mock_raw)
            RAW_FUNCTIONS['test_func2'].assert_called_once_with(self.mock_raw)
            
            # Result should be the processed raw object
            assert result == self.mock_raw
    
    def test_execute_unknown_function(self):
        """Test handling of unknown function names."""
        self.setUp()
        
        function_names = ['unknown_function', 'another_unknown']
        
        # Should not raise exception, should log warnings
        with patch('sovabids.transformations.LOGGER') as mock_logger:
            result = execute_safe_raw_functions(function_names, self.mock_raw)
            
            # Should return original raw object
            assert result == self.mock_raw
            
            # Should log warnings
            assert mock_logger.warning.call_count == 2
    
    def test_function_error_handling(self):
        """Test error handling when functions raise exceptions."""
        self.setUp()
        
        def failing_function(raw):
            raise ValueError("Test error")
        
        with patch.dict(RAW_FUNCTIONS, {'failing_func': failing_function}):
            
            with patch('sovabids.transformations.LOGGER') as mock_logger:
                result = execute_safe_raw_functions(['failing_func'], self.mock_raw)
                
                # Should return original raw object despite error
                assert result == self.mock_raw
                
                # Should log error
                mock_logger.error.assert_called_once()

class TestBuiltInFunctions:
    """Test the specific built-in raw processing functions."""
    
    def setUp(self):
        """Set up mock raw object for testing."""
        # Create a more realistic mock
        self.mock_raw = Mock()
        self.mock_raw.info = {
            'sfreq': 1000.0,
            'nchan': 6,
            'bads': ['T7', 'T8']
        }
        self.mock_raw.ch_names = ['Fp1', 'Fp2', 'F3', 'F4', 'T7', 'T8']
        self.mock_raw.times = np.linspace(0, 600, 600000)  # 10 minutes at 1000Hz
        
        # Mock MNE functions
        self.mock_raw.drop_channels = Mock(return_value=None)
        self.mock_raw.notch_filter = Mock(return_value=None)
        self.mock_raw.resample = Mock(return_value=None)
        self.mock_raw.crop = Mock(return_value=None)
        self.mock_raw.set_montage = Mock(return_value=None)
    
    def test_print_info_function(self):
        """Test the print_info function."""
        self.setUp()
        
        from sovabids.transformations import print_raw_info
        
        # Capture print output
        with patch('builtins.print') as mock_print:
            result = print_raw_info(self.mock_raw)
            
            # Should return the same raw object
            assert result == self.mock_raw
            
            # Should have printed information
            assert mock_print.call_count > 0
            
            # Check that info was printed
            printed_text = ' '.join([str(call.args[0]) for call in mock_print.call_args_list])
            assert 'Sampling frequency' in printed_text
            assert '1000' in printed_text
    
    def test_drop_bad_channels_function(self):
        """Test the drop_bad_channels function."""
        self.setUp()
        
        from sovabids.transformations import drop_bad_channels
        
        result = drop_bad_channels(self.mock_raw)
        
        # Should return the same raw object
        assert result == self.mock_raw
        
        # Should have called drop_channels with bad channels
        self.mock_raw.drop_channels.assert_called_once_with(['T7', 'T8'])
    
    def test_drop_bad_channels_no_bads(self):
        """Test drop_bad_channels when no bad channels exist."""
        self.setUp()
        self.mock_raw.info['bads'] = []
        
        from sovabids.transformations import drop_bad_channels
        
        result = drop_bad_channels(self.mock_raw)
        
        # Should return the same raw object
        assert result == self.mock_raw
        
        # Should not have called drop_channels
        self.mock_raw.drop_channels.assert_not_called()
    
    def test_filter_functions(self):
        """Test the notch filter functions."""
        self.setUp()
        
        from sovabids.transformations import filter_line_noise_50hz, filter_line_noise_60hz
        
        # Test 50Hz filter
        result = filter_line_noise_50hz(self.mock_raw)
        assert result == self.mock_raw
        self.mock_raw.notch_filter.assert_called_with(freqs=50, picks='eeg', method='fir', verbose=False)
        
        # Reset mock
        self.mock_raw.notch_filter.reset_mock()
        
        # Test 60Hz filter
        result = filter_line_noise_60hz(self.mock_raw)
        assert result == self.mock_raw
        self.mock_raw.notch_filter.assert_called_with(freqs=60, picks='eeg', method='fir', verbose=False)
    
    def test_resample_function(self):
        """Test the resample function."""
        self.setUp()
        
        from sovabids.transformations import resample_500hz
        
        # Test when resampling is needed
        result = resample_500hz(self.mock_raw)
        assert result == self.mock_raw
        self.mock_raw.resample.assert_called_once_with(500)
        
        # Test when no resampling needed
        self.mock_raw.resample.reset_mock()
        self.mock_raw.info['sfreq'] = 500
        
        result = resample_500hz(self.mock_raw)
        assert result == self.mock_raw
        self.mock_raw.resample.assert_not_called()
    
    def test_crop_function(self):
        """Test the crop function."""
        self.setUp()
        
        from sovabids.transformations import crop_to_10min
        
        # Test cropping long recording
        result = crop_to_10min(self.mock_raw)
        assert result == self.mock_raw
        self.mock_raw.crop.assert_called_once_with(tmax=600)  # 10 minutes
        
        # Test cropping short recording
        self.mock_raw.crop.reset_mock()
        self.mock_raw.times = np.linspace(0, 300, 300000)  # 5 minutes
        
        result = crop_to_10min(self.mock_raw)
        assert result == self.mock_raw
        self.mock_raw.crop.assert_called_once_with(tmax=300)  # Keep original length
    
    def test_set_montage_function(self):
        """Test the set montage function."""
        self.setUp()
        
        from sovabids.transformations import set_standard_1020_montage
        
        # Test that the function completes without error (even if MNE import fails)
        # This tests the error handling path
        result = set_standard_1020_montage(self.mock_raw)
        
        # Should return the same raw object
        assert result == self.mock_raw
        
        # Note: We can't easily test the successful MNE path without actual MNE
        # The important thing is that the function handles errors gracefully
    
    def test_set_montage_function_with_mock_logger(self):
        """Test the set montage function logs appropriately."""
        self.setUp()
        
        from sovabids.transformations import set_standard_1020_montage
        
        with patch('sovabids.transformations.LOGGER') as mock_logger:
            result = set_standard_1020_montage(self.mock_raw)
            
            # Should return raw object
            assert result == self.mock_raw
            
            # Should have logged something (either success or warning)
            assert mock_logger.info.called or mock_logger.warning.called

class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_transformations(self):
        """Test behavior with empty transformation operations."""
        operations = {}
        variables = {'test': 'value'}
        
        results = apply_safe_transformations(operations, variables)
        assert results == {}
    
    def test_none_operations(self):
        """Test behavior with None operations."""
        # This should not cause errors
        results = apply_safe_transformations(None, {})
        # Function should handle this gracefully
        assert results == {}
    
    def test_empty_function_list(self):
        """Test executing empty function list."""
        mock_raw = Mock()
        
        result = execute_safe_raw_functions([], mock_raw)
        assert result == mock_raw
    
    def test_none_function_list(self):
        """Test executing None function list."""
        mock_raw = Mock()
        
        # Should handle gracefully
        result = execute_safe_raw_functions(None, mock_raw)
        # Implementation should handle this case
        assert result == mock_raw

# Integration tests would go in test_rules.py or a separate integration test file
class TestTransformationIntegration:
    """Test integration with the rules system."""
    
    def test_integration_placeholder(self):
        """Placeholder for integration tests."""
        # These would test the full integration with rules.py
        # Testing apply_rules_to_single_file with transformation features
        pass

if __name__ == '__main__':
    # Run tests with: python -m pytest tests/test_transformations.py -v
    pytest.main([__file__, '-v'])