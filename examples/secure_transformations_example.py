"""
Example demonstrating secure transformations in Sovabids.

This example shows how to use the new secure transformation system
that replaces the deprecated code execution functionality.
"""

import os
import tempfile
import yaml
from sovabids.rules import apply_rules
from sovabids.datasets import create_dummy_dataset
from sovabids.transformations import get_available_functions, get_function_documentation

def create_secure_rules_example():
    """Create an example rule file using secure transformations."""
    
    rules = {
        'entities': {
            'task': 'resting',
            'session': 'ses1'
        },
        'dataset_description': {
            'Name': 'SecureTransformationDemo',
            'Authors': ['Alice', 'Bob']
        },
        'sidecar': {
            'EEGReference': 'FCz',
            'PowerLineFrequency': 50
        },
        'channels': {
            'name': {
                'heo': 'HEO',
                'veo': 'VEO'
            },
            'type': {
                'HEO': 'HEOG',
                'VEO': 'VEOG'
            }
        },
        'non-bids': {
            'eeg_extension': '.vhdr',
            'path_analysis': {
                'pattern': 'sub-%entities.subject%/ses-%entities.session%/%entities.task%_data.vhdr',
                'operation': {
                    # Secure string concatenation examples
                    'entities.subject': '[subject_prefix] + [subject_number]',
                    'entities.run': '[task]_[run_number]',
                    'dataset_description.Name': '[dataset_name] + [version]'
                }
            },
            'raw_functions': [
                # Safe raw object processing functions
                'print_info',                    # Print information about raw object
                'drop_bad_channels',            # Remove bad channels
                'filter_line_noise_50hz',       # Apply 50Hz notch filter
                'set_montage_standard_1020',    # Set standard montage
                'resample_500hz'                # Resample to 500Hz
            ],
            'file_filter': [
                {'include': 'resting'},
                {'exclude': '_PREP'},
                {'exclude': '_processed'}
            ],
            'output_format': 'BrainVision'
        }
    }
    
    return rules

def demonstrate_string_concatenation():
    """Demonstrate secure string concatenation functionality."""
    
    print("=== String Concatenation Examples ===")
    
    from sovabids.transformations import safe_string_concatenation
    
    # Example variables that might be extracted from file paths
    variables = {
        'subject_prefix': 'sub',
        'subject_number': '001',
        'task': 'resting',
        'run_number': '01',
        'session_prefix': 'ses',
        'session_id': '1',
        'dataset_name': 'MyStudy',
        'version': 'v2',
        'entities': {
            'subject': '001',
            'session': 'ses1',
            'task': 'resting'
        }
    }
    
    # Test different concatenation patterns
    examples = [
        ("[subject_prefix] + [subject_number]", "Simple concatenation"),
        ("[task]_[run_number]", "Underscore separator"),
        ("[session_prefix] + [session_id]", "Prefix with ID"),
        ("[dataset_name] + [version]", "Dataset versioning"),
        ("[entities.task]_processed", "Nested variable access")
    ]
    
    for expression, description in examples:
        result = safe_string_concatenation(expression, variables)
        print(f"{description:25}: {expression:30} -> {result}")

def demonstrate_raw_functions():
    """Demonstrate available raw processing functions."""
    
    print("\n=== Available Raw Processing Functions ===")
    
    functions = get_available_functions()
    docs = get_function_documentation()
    
    for func_name in functions:
        doc = docs.get(func_name, "No documentation available")
        print(f"{func_name:25}: {doc}")

def create_migration_example():
    """Show how to migrate from legacy code execution to secure transformations."""
    
    print("\n=== Migration Example ===")
    
    # Old insecure format (DON'T USE)
    old_rules = {
        'non-bids': {
            'code_execution': [
                'print(raw.info)',
                'raw.drop_channels(raw.info["bads"])',
                'raw.notch_filter(freqs=50, picks="eeg")',
                'raw.resample(500)'
            ]
        }
    }
    
    # New secure format (USE THIS)
    new_rules = {
        'non-bids': {
            'raw_functions': [
                'print_info',
                'drop_bad_channels', 
                'filter_line_noise_50hz',
                'resample_500hz'
            ]
        }
    }
    
    print("OLD FORMAT (INSECURE - DON'T USE):")
    print(yaml.dump(old_rules, default_flow_style=False, indent=2))
    
    print("NEW FORMAT (SECURE - USE THIS):")
    print(yaml.dump(new_rules, default_flow_style=False, indent=2))

def run_secure_conversion_example():
    """Run a complete example using secure transformations."""
    
    print("\n=== Complete Secure Conversion Example ===")
    
    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        source_dir = os.path.join(temp_dir, 'source')
        bids_dir = os.path.join(temp_dir, 'bids')
        
        # Create dummy dataset
        print("Creating dummy dataset...")
        create_dummy_dataset(source_dir, n_subjects=2, n_sessions=1)
        
        # Create secure rules
        rules = create_secure_rules_example()
        
        # Add context variables for string concatenation demonstration
        rules['non-bids']['path_analysis']['context'] = {
            'subject_prefix': 'sub',
            'subject_number': '001',
            'task': 'resting',
            'run_number': '01'
        }
        
        print(f"Source directory: {source_dir}")
        print(f"BIDS directory: {bids_dir}")
        
        # Apply rules with secure transformations
        try:
            print("Applying secure transformations...")
            mappings = apply_rules(
                source_path=source_dir,
                bids_path=bids_dir,
                rules=rules
            )
            
            print("✓ Secure transformations applied successfully!")
            print(f"Generated {len(mappings.get('Individual', []))} file mappings")
            
        except Exception as e:
            print(f"Error during conversion: {e}")

def main():
    """Run all examples."""
    
    print("Sovabids Secure Transformations Example")
    print("="*50)
    
    # Demonstrate string concatenation
    demonstrate_string_concatenation()
    
    # Show available raw functions
    demonstrate_raw_functions()
    
    # Show migration example
    create_migration_example()
    
    # Run complete example
    run_secure_conversion_example()
    
    print("\n" + "="*50)
    print("Examples completed successfully!")
    print("\nFor more information, see:")
    print("- Documentation: https://sovabids.readthedocs.io/en/latest/transformations.html")
    print("- Security Notice: https://sovabids.readthedocs.io/en/latest/security_notice.html")

if __name__ == "__main__":
    main()