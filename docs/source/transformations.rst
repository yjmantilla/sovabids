Built-in Transformations
========================

Sovabids provides secure built-in transformations to replace the deprecated code execution functionality. These transformations are designed to be safe while providing the flexibility needed for common EEG to BIDS conversion tasks.

String Concatenation
--------------------

For path analysis operations, you can use safe string concatenation with the ``[variable]`` syntax:

Basic Concatenation
^^^^^^^^^^^^^^^^^^^

The `[variable]` syntax references variables that are available in the current context (extracted from file paths, rule definitions, etc.):

.. code-block:: yaml

    non-bids:
        path_analysis:
            operation:
                # These [variables] must exist in the context
                entities.subject: "[subject_prefix] + [subject_number]"
                entities.session: "[session_type]_[session_id]"

**Important**: The variables inside `[brackets]` must be available in the context. They come from:

1. **Path analysis extraction** (from your file path patterns)
2. **Existing rule values** (from other parts of your rule file)
3. **Previously extracted entities** (from earlier processing steps)

This safely concatenates variables without using dangerous ``eval()`` functions.

Variable Access
^^^^^^^^^^^^^^^

You can access nested variables using dot notation:

.. code-block:: yaml

    non-bids:
        path_analysis:
            operation:
                entities.task: "[entities.task]_processed"
                dataset_description.Name: "[dataset.name] + [dataset.version]"

Examples
^^^^^^^^

.. code-block:: yaml

    # Variables extracted from file path or context:
    # subject_prefix = "sub"
    # subject_number = "001"  
    # session_type = "rest"
    # session_id = "01"
    
    # Simple concatenation
    entities.subject: "[subject_prefix] + [subject_number]"    # Result: "sub001"
    
    # With underscores  
    entities.session: "[session_type]_[session_id]"           # Result: "rest_01"
    
    # Multiple variables
    entities.run: "[entities.task] + [entities.session]"      # Result: "restingses1"
    
    # Accessing nested values from extracted patterns
    entities.subject: "[entities.subject]_processed"          # Result: "001_processed"

Raw Processing Functions
------------------------

Instead of arbitrary code execution, use predefined safe functions for raw object processing:

Basic Usage
^^^^^^^^^^^

.. code-block:: yaml

    non-bids:
        raw_functions:
            - print_info
            - drop_bad_channels
            - filter_line_noise_50hz

Available Functions
^^^^^^^^^^^^^^^^^^^

Information and Debugging
~~~~~~~~~~~~~~~~~~~~~~~~~

* **print_info**: Print information about the raw object (sampling rate, channels, duration)

Data Cleaning
~~~~~~~~~~~~~

* **drop_bad_channels**: Remove channels marked as bad in the raw object
* **set_montage_standard_1020**: Apply standard 10-20 montage for EEG channels

Filtering
~~~~~~~~~

* **filter_line_noise_50hz**: Apply 50Hz notch filter for European line noise
* **filter_line_noise_60hz**: Apply 60Hz notch filter for North American line noise

Preprocessing  
~~~~~~~~~~~~~

* **resample_500hz**: Resample data to 500Hz
* **crop_to_10min**: Crop recording to first 10 minutes

Complete Example
----------------

Here's a complete rule file using the new secure transformations:

.. code-block:: yaml

    entities:
        task: resting
        session: ses1

    dataset_description:
        Name: MyDataset
        Authors:
            - Alice
            - Bob

    sidecar:
        EEGReference: FCz
        PowerLineFrequency: 50

    channels:
        name:
            heo: HEO
            veo: VEO
        type:
            HEO: HEOG
            VEO: VEOG

    non-bids:
        eeg_extension: .vhdr
        path_analysis:
            pattern: _data/%dataset_description.Name%/ses-%entities.session%/%entities.task%/sub-%entities.subject%.vhdr
            operation:
                entities.subject: "[subject_prefix] + [subject_number]"
                entities.run: "[task]_[run_number]"
        raw_functions:
            - print_info
            - drop_bad_channels
            - filter_line_noise_50hz
            - set_montage_standard_1020
        file_filter:
            - include: eyesClosed
            - exclude: _PREP
        output_format: 'BrainVision'

Migration from Legacy Code Execution
------------------------------------

If you were using the old ``code_execution`` functionality, here's how to migrate:

Old Format (DEPRECATED - SECURITY RISK)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

    # DON'T USE - REMOVED FOR SECURITY
    non-bids:
        code_execution:
            - print(raw.info)
            - raw.drop_channels(raw.info['bads'])
            - raw.notch_filter(freqs=50, picks='eeg')

New Secure Format
^^^^^^^^^^^^^^^^^

.. code-block:: yaml

    # USE THIS INSTEAD
    non-bids:
        raw_functions:
            - print_info
            - drop_bad_channels  
            - filter_line_noise_50hz

Adding Custom Functions
-----------------------

If you need functionality not provided by the built-in functions, you can fork the repository and add new functions:

1. **Fork the repository** on GitHub

2. **Add your function** to ``sovabids/transformations.py``:

   .. code-block:: python

       @register_raw_function("my_custom_filter")
       def my_custom_filter(raw: BaseRaw) -> BaseRaw:
           \"\"\"Apply custom bandpass filter.\"\"\"
           raw.filter(l_freq=1.0, h_freq=40.0, picks='eeg')
           LOGGER.info("Applied custom 1-40Hz bandpass filter")
           return raw

3. **Use your function** in rule files:

   .. code-block:: yaml

       non-bids:
           raw_functions:
               - my_custom_filter

4. **Submit a pull request** if your function would be useful for others

Security Benefits
-----------------

The new transformation system provides several security advantages:

* **No arbitrary code execution**: Only predefined, vetted functions can be called
* **Input validation**: All string operations are safely parsed and validated
* **Sandboxed operations**: Functions operate in a controlled environment
* **Audit trail**: All transformations are logged for debugging and security

* **Extensible design**: New functions can be added safely through the plugin system

Best Practices
--------------

1. **Use descriptive function names**: Choose names that clearly indicate what the function does
2. **Test thoroughly**: Always test your transformations with sample data
3. **Document functions**: Provide clear documentation for any custom functions
4. **Follow BIDS conventions**: Ensure transformations produce BIDS-compliant output
5. **Log appropriately**: Use logging to track transformation steps for debugging

Getting Help
------------

If you need help migrating from legacy code execution or implementing new transformations:

1. Check the `Security Changes documentation <../SECURITY_CHANGES.md>`_
2. Review available built-in functions above
3. Open an issue on GitHub describing your use case
4. Contact maintainers for guidance on safe implementation patterns