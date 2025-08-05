# Security Changes in Sovabids

## Overview

This document outlines critical security changes made to Sovabids to address code execution vulnerabilities. These changes were implemented to protect users from potential security risks while maintaining the core functionality of the EEG to BIDS conversion system.

## Changes Made

### 1. Removed Code Execution Functionality

**Files affected:**
- `sovabids/rules.py:254-270`

**What was removed:**
- The `code_execution` feature in rule files that allowed arbitrary Python code execution
- All `exec()` calls that executed user-provided code

**Security risk addressed:**
- Arbitrary code execution from rule files could lead to complete system compromise
- Malicious rule files could execute system commands, access sensitive files, or install malware

**Migration path:**
- Use built-in transformation functions instead of custom code
- Contact maintainers if specific functionality is needed

### 2. Removed Expression Evaluation

**Files affected:**
- `sovabids/rules.py:81-85`

**What was removed:**
- `eval()` calls for processing mathematical expressions in path analysis operations
- Dynamic expression evaluation from rule configuration

**Security risk addressed:**
- Expression injection attacks through malicious rule files
- Code execution through crafted mathematical expressions

**Migration path:**
- Use static configuration values instead of dynamic expressions
- Contact maintainers for alternative approaches to complex path transformations

### 3. Fixed Web Interface Vulnerabilities

**Files affected:**
- `front/app/app.py:222, 266`

**What was changed:**
- Replaced `eval(request.form.get('rules'))` with safe YAML parsing using `yaml.safe_load()`
- Added error handling for malformed YAML input
- Implemented input validation

**Security risk addressed:**
- Remote Code Execution (RCE) through web form submissions
- Direct code injection through malicious form data

**Migration path:**
- Ensure rule inputs are valid YAML format
- Use the corrected web interface which now safely parses configuration

### 4. Upgraded YAML Loading

**Files affected:**
- `sovabids/rules.py:159`

**What was changed:**
- Replaced `yaml.load(f, yaml.FullLoader)` with `yaml.safe_load(f)`
- Eliminated potential code execution through malicious YAML files

**Security risk addressed:**
- YAML deserialization attacks
- Code execution through crafted YAML files containing Python objects

**Migration path:**
- Ensure YAML files contain only data, not Python code or objects
- Files should continue to work without changes if they only contain configuration data

### 5. Fixed Shell Command Injection

**Files affected:**
- `tests/test_bids.py:115, 223`

**What was changed:**
- Replaced `os.system()` calls with `subprocess.run()` using shell=False
- Eliminated shell injection vulnerabilities in test code

**Security risk addressed:**
- Shell command injection through crafted file paths
- Potential privilege escalation in test environments

**Migration path:**
- Tests should continue to work without modification
- Any custom scripts using similar patterns should be updated

## Impact on Functionality

### Features Removed:
1. **Custom code execution in rule files** - No longer supported for security reasons
2. **Dynamic expression evaluation** - Mathematical expressions in path operations are no longer supported
3. **Unsafe YAML loading** - Only safe, data-only YAML parsing is now supported

### Features Preserved:
1. **Core EEG to BIDS conversion** - All primary functionality remains intact
2. **Rule-based configuration** - Static rule files continue to work
3. **Multiple interfaces** - Python API, CLI, RPC, and web GUI all remain functional
4. **Path pattern matching** - Placeholder and regex patterns still work
5. **Built-in transformations** - All existing safe transformation functions remain available

## Upgrade Instructions

### For Users:

1. **Review existing rule files:**
   - Remove any `code_execution` sections
   - Replace dynamic expressions with static values
   - Ensure YAML files contain only configuration data

2. **Test conversions:**
   - Run test conversions to ensure your workflows still work
   - Contact maintainers if critical functionality is missing

3. **Update automation:**
   - Review any scripts that generate rule files
   - Ensure generated YAML is valid and contains no code

### For Developers:

1. **Update integrations:**
   - Replace any direct `eval()` or `exec()` calls with safe alternatives
   - Use `yaml.safe_load()` instead of `yaml.load()`
   - Use `subprocess.run()` with `shell=False` instead of `os.system()`

2. **Security best practices:**
   - Always validate user input before processing
   - Use parameterized queries/commands instead of string concatenation
   - Implement proper access controls for file operations

## Getting Help

If you encounter issues with these security changes or need alternative approaches for removed functionality:

1. **Check the documentation** for built-in transformation functions
2. **Open an issue** on the GitHub repository describing your use case
3. **Contact maintainers** for guidance on secure implementation patterns

## Security Contact

For security-related issues or questions about these changes, please contact the maintainers through the project's GitHub repository.

---

**Note:** These changes prioritize security over backward compatibility. While some functionality has been removed, the core EEG to BIDS conversion capabilities remain fully functional and secure.