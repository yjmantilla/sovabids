Security Notice
===============

.. danger::

    **Important Security Update**
    
    Several security-critical features have been removed from Sovabids to protect users from potential code execution vulnerabilities. Please review this notice carefully if you are upgrading from a previous version.

Removed Features
----------------

code_execution
^^^^^^^^^^^^^^

The ``code_execution`` functionality in rule files has been **completely removed** due to critical security risks:

- **Risk**: Allowed arbitrary Python code execution from rule files
- **Impact**: Could lead to complete system compromise, data theft, and malware installation
- **Status**: **REMOVED** - Will log warnings if found in rule files

**Migration**: Use built-in transformation functions instead. Contact maintainers if you need specific functionality.

Expression Evaluation
^^^^^^^^^^^^^^^^^^^^^

Dynamic expression evaluation in path analysis operations has been **removed**:

- **Risk**: Code injection through crafted mathematical expressions
- **Impact**: Potential code execution through malicious rule files
- **Status**: **REMOVED** - Operations with expressions will be ignored

**Migration**: Use static configuration values instead of dynamic expressions.

Security Improvements
---------------------

Web Interface
^^^^^^^^^^^^^

- **Fixed**: Remote Code Execution (RCE) vulnerability in web forms
- **Change**: Replaced ``eval()`` with safe YAML parsing
- **Impact**: Forms now safely parse configuration without security risks

YAML Loading
^^^^^^^^^^^^

- **Fixed**: YAML deserialization vulnerabilities  
- **Change**: Replaced unsafe ``yaml.load()`` with ``yaml.safe_load()``
- **Impact**: Only safe, data-only YAML files are now supported

Shell Commands
^^^^^^^^^^^^^^

- **Fixed**: Shell injection vulnerabilities in test code
- **Change**: Replaced ``os.system()`` with safe ``subprocess.run()``
- **Impact**: Eliminated command injection risks

Upgrade Instructions
--------------------

1. **Review Rule Files**
   
   Remove any ``code_execution`` sections from your rule files:
   
   .. code-block:: yaml
   
       # REMOVE THIS:
       non-bids:
           code_execution:
               - print(raw.info)
               - some_custom_function()
   
   Replace with built-in transformation functions or contact maintainers for alternatives.

2. **Test Your Workflows**
   
   Run test conversions to ensure your workflows still function correctly after the security updates.

3. **Update Integrations**
   
   If you have custom scripts or integrations:
   
   - Use ``yaml.safe_load()`` instead of ``yaml.load()``
   - Replace ``eval()`` and ``exec()`` calls with safe alternatives
   - Use ``subprocess.run()`` with ``shell=False`` instead of ``os.system()``

Getting Help
------------

If you encounter issues after the security update:

1. Check the `Security Changes document <../SECURITY_CHANGES.md>`_ for detailed migration guidance
2. Open an issue on the GitHub repository describing your use case
3. Contact maintainers for assistance with secure implementation patterns

**Remember**: These changes prioritize security over backward compatibility. While some functionality has been removed, the core EEG to BIDS conversion capabilities remain fully functional and secure.