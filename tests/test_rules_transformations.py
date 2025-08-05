"""
Integration tests for transformations with the rules system.

Tests the integration of secure transformations with the existing rules.py functionality.
"""

import pytest
import tempfile
import os
import yaml
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from sovabids.rules import apply_rules_to_single_file, get_info_from_path, load_rules
from sovabids.transformations import RAW_FUNCTIONS
from sovabids.datasets import get_dummy_raw,save_dummy_vhdr

class TestRulesTransformationIntegration:
    """Test integration of transformations with rules system."""
    
    def create_mock_raw(self):
        """Create a mock raw object for testing."""

        raw,new_events = get_dummy_raw()
        # mock_raw = MagicMock()
        # mock_raw.info = {
        #     'sfreq': 1000.0,
        #     'nchan': 6,
        #     'bads': ['T7', 'T8']
        # }
        # mock_raw.ch_names = ['Fp1', 'Fp2', 'F3', 'F4', 'T7', 'T8']
        # mock_raw.times = np.linspace(0, 60, 60000)  # 1 minute at 1000Hz
        # mock_raw.filenames = ['/test/file.eeg']
        # mock_raw.last_samp = 60000
        
        # # Mock methods that get called
        # mock_raw.drop_channels = Mock(return_value=None)
        # mock_raw.notch_filter = Mock(return_value=None)
        # mock_raw.resample = Mock(return_value=None)
        # mock_raw.crop = Mock(return_value=None)
        # mock_raw.set_montage = Mock(return_value=None)
        # mock_raw.set_channel_types = Mock(return_value=None)
        
        return raw
    
    def test_path_analysis_transformations(self):
        """Test string transformations in path analysis operations."""
        
        # Test data
        path = "/data/study1/sub-001/ses-baseline/task-rest_run-01.eeg"
        
        rules = {
            'entities': {
                'task': 'resting',
            },
            'non-bids': {
                'path_analysis': {
                    'pattern': '/data/%study%/sub-%subject%/ses-%session%/task-%origTask%_run-%run%.eeg',
                    'operation': {
                        'entities.subject': '[subject]',
                        'entities.session': 'S[session]',
                        'entities.task': '[entities.task]',  # From rule definition
                        'entities.run': '[run]',
                        'custom_field': '[study] + [origTask]'  # String concatenation
                    }
                }
            }
        }
        
        # Apply path analysis with transformations
        result_rules = get_info_from_path(path, rules)
        
        # Check that transformations were applied
        assert result_rules['entities']['subject'] == '001'
        assert result_rules['entities']['session'] == 'Sbaseline' 
        assert result_rules['entities']['task'] == 'resting'  # From rule file
        assert result_rules['entities']['run'] == '01'
        assert result_rules.get('custom_field') == 'study1rest'  # Concatenated
    
    def test_path_analysis_missing_variables(self):
        """Test path analysis with missing variables in transformations."""
        
        path = "/data/study1/sub-001/recording.eeg"
        
        rules = {
            'non-bids': {
                'path_analysis': {
                    'pattern': '/data/%study%/sub-%subject%/recording.eeg',
                    'operation': {
                        'entities.subject': '[subject]',
                        'entities.session': '[missingVar]',  # This variable doesn't exist
                        'entities.run': '[subject] + [missingVar]'  # Mixed existing/missing
                    }
                }
            }
        }
        
        # Should not raise exception, should handle missing variables gracefully
        with patch('sovabids.transformations.LOGGER') as mock_logger:
            result_rules = get_info_from_path(path, rules)
            
            # Existing variable should work
            assert result_rules['entities']['subject'] == '001'
            
            # Missing variable should keep placeholder
            assert result_rules['entities']['session'] == '[missingVar]'
            assert result_rules['entities']['run'] == '001[missingVar]'
    
    def test_raw_functions_integration(self):
        """Test integration of raw processing functions with apply_rules_to_single_file."""
                
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.vhdr', delete=False) as f:
            test_file = f.name
            example_fpath = save_dummy_vhdr(test_file)

        # Rules with raw functions
        rules = {
            'entities': {
                'subject': '001',
                'session': 'ses1',
                'task': 'rest'
            },
            'non-bids': {
                'eeg_extension': '.vhdr',
                'raw_functions': [
                    'print_info',
                    'drop_bad_channels',
                    'filter_line_noise_50hz'
                ]
            }
        }
        
        result = apply_rules_to_single_file(
            file=test_file,
            rules=rules,
            bids_path='/tmp/bids',
            write=False
        )

        if os.path.exists(test_file):
            os.unlink(test_file)

    def test_legacy_code_execution_warning(self):
        """Test that legacy code_execution triggers warning and is removed."""
        
        # Setup mocks
        mock_raw = self.create_mock_raw()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.vhdr', delete=False) as f:
            test_file = f.name
            example_fpath = save_dummy_vhdr(test_file)
        
        try:
            # Rules with legacy code_execution
            rules = {
                'entities': {
                    'subject': '001',
                    'session': 'ses1',
                    'task': 'rest'
                },
                'non-bids': {
                    'eeg_extension': '.vhdr',
                    'code_execution': [  # Legacy format
                        'print(raw.info)',
                        'raw.drop_channels(raw.info["bads"])'
                    ]
                }
            }
            
            # Should log warning and remove code_execution
            with patch('sovabids.rules.LOGGER') as mock_logger:
                result = apply_rules_to_single_file(
                    file=test_file,
                    rules=rules,
                    bids_path='/tmp/bids',
                    write=False
                )
                
                # Check that warning was logged
                mock_logger.warning.assert_called()
                warning_message = mock_logger.warning.call_args[0][0]
                assert 'Legacy code_execution functionality has been removed' in warning_message
                assert 'raw_functions' in warning_message
        
        finally:
            # Clean up
            if os.path.exists(test_file):
                os.unlink(test_file)
    
    def test_load_rules_with_transformations(self):
        """Test loading rules from YAML file with transformation syntax."""
        
        # Create temporary rules file
        rules_data = {
            'entities': {
                'task': 'resting',
                'session': 'ses1'
            },
            'non-bids': {
                'path_analysis': {
                    'pattern': '/data/%study%/sub-%subject%/recording.eeg',
                    'operation': {
                        'entities.subject': '[subject]',
                        'entities.session': '[entities.session]',
                        'custom_id': '[study] + [subject]'
                    }
                },
                'raw_functions': [
                    'print_info',
                    'drop_bad_channels'
                ]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(rules_data, f)
            rules_file = f.name
        
        try:
            # Load rules
            loaded_rules = load_rules(rules_file)
            
            # Check that structure is preserved
            assert loaded_rules['entities']['task'] == 'resting'
            assert loaded_rules['non-bids']['raw_functions'] == ['print_info', 'drop_bad_channels']
            
            # Check transformation operations
            operations = loaded_rules['non-bids']['path_analysis']['operation']
            assert operations['entities.subject'] == '[subject]'
            assert operations['custom_id'] == '[study] + [subject]'
        
        finally:
            # Clean up
            if os.path.exists(rules_file):
                os.unlink(rules_file)
    
    def test_transformation_error_handling(self):
        """Test error handling in transformations during rule application."""
        
        path = "/data/study1/sub-001/recording.eeg"
        
        # Rules with problematic transformations
        rules = {
            'non-bids': {
                'path_analysis': {
                    'pattern': '/data/%study%/sub-%subject%/recording.eeg',
                    'operation': {
                        'valid_transform': '[subject]',
                        'problematic_transform': '[missing_var]'
                    }
                }
            }
        }
        
        # Should handle errors gracefully
        with patch('sovabids.transformations.LOGGER') as mock_logger:
            result_rules = get_info_from_path(path, rules)
            
            # Valid transformation should work
            assert result_rules.get('valid_transform') == '001'
            
            # Invalid transformation should be handled gracefully
            # (specific behavior depends on implementation)
    
    def test_nested_variable_access_in_rules(self):
        """Test accessing nested variables in rule transformations."""
        
        path = "/data/MyStudy/sub-001/ses-baseline/recording.eeg"
        
        rules = {
            'entities': {
                'task': 'resting'
            },
            'dataset_description': {
                'Name': 'TestStudy'
            },
            'non-bids': {
                'path_analysis': {
                    'pattern': '/data/%study%/sub-%subject%/ses-%session%/recording.eeg',
                    'operation': {
                        'entities.subject': '[subject]',
                        'entities.task': '[entities.task]',  # From entities section
                        'study_name': '[dataset_description.Name]',  # From dataset_description
                        'combined': '[study] + [entities.task]'  # Mixed sources
                    }
                }
            }
        }
        
        result_rules = get_info_from_path(path, rules)
        
        # Check nested access works
        assert result_rules['entities']['subject'] == '001'
        assert result_rules['entities']['task'] == 'resting'
        assert result_rules.get('study_name') == 'TestStudy'
        assert result_rules.get('combined') == 'MyStudyresting'

class TestTransformationSafety:
    """Test security aspects of the transformation system."""
    
    def test_no_code_execution_in_transformations(self):
        """Test that transformations don't allow code execution."""
        
        # Potentially dangerous transformation attempts
        dangerous_operations = {
            'malicious1': '[__import__("os").system("echo test")]',
            'malicious2': '[eval("1+1")]',
            'malicious3': '[exec("print(\'test\')")]'
        }
        
        variables = {'safe_var': 'safe_value'}
        
        from sovabids.transformations import apply_safe_transformations
        
        # Should not execute any code, should treat as literal strings
        results = apply_safe_transformations(dangerous_operations, variables)
        
        # All should remain as placeholders (not executed)
        for key, result in results.items():
            assert '__import__' in result or 'eval' in result or 'exec' in result
            # Should not contain execution results
    
    def test_function_registry_safety(self):
        """Test that only registered functions can be executed."""
        
        mock_raw = Mock()
        
        # Try to execute non-existent/dangerous function names
        dangerous_functions = [
            '__import__',
            'eval',
            'exec',
            'open',
            'compile',
            'non_existent_function'
        ]
        
        from sovabids.transformations import execute_safe_raw_functions
        
        with patch('sovabids.transformations.LOGGER') as mock_logger:
            result = execute_safe_raw_functions(dangerous_functions, mock_raw)
            
            # Should return original raw object
            assert result == mock_raw
            
            # Should log warnings for unknown functions
            assert mock_logger.warning.call_count == len(dangerous_functions)

class TestPerformance:
    """Test performance aspects of transformations."""
    
    def test_transformation_performance(self):
        """Test that transformations complete in reasonable time."""
        import time
        
        # Large set of transformations
        operations = {f'var_{i}': f'[prefix] + [suffix_{i%10}]' for i in range(1000)}
        variables = {'prefix': 'test'}
        variables.update({f'suffix_{i}': f'_{i}' for i in range(10)})
        
        from sovabids.transformations import apply_safe_transformations
        
        start_time = time.time()
        results = apply_safe_transformations(operations, variables)
        end_time = time.time()
        
        # Should complete in reasonable time (less than 1 second for 1000 operations)
        assert (end_time - start_time) < 1.0
        assert len(results) == 1000

if __name__ == '__main__':
    pytest.main([__file__, '-v'])