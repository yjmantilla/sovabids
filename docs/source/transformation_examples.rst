Transformation Examples
======================

This page provides detailed examples of how the new secure transformation system works, with concrete scenarios showing where variables come from and how they're used.

Understanding Variable Context
------------------------------

The `[variable]` syntax references variables that exist in the **context** at the time of processing. Here's where these variables come from:

Variable Sources
^^^^^^^^^^^^^^^^

1. **From path pattern extraction**:
   
   If your file path is: ``/data/study1/sub-001/ses-baseline/task-rest_run-01.eeg``
   
   And your pattern is: ``/data/%study%/sub-%subject%/ses-%session%/task-%task%_run-%run%.eeg``
   
   Then these variables become available:
   - ``study`` = "study1"
   - ``subject`` = "001" 
   - ``session`` = "baseline"
   - ``task`` = "rest"
   - ``run`` = "01"

2. **From rule file definitions**:
   
   From your rule file:
   
   .. code-block:: yaml
   
       entities:
           task: resting
           session: ses1
       
       dataset_description:
           Name: MyStudy
   
   These become available as:
   - ``entities.task`` = "resting"
   - ``entities.session`` = "ses1" 
   - ``dataset_description.Name`` = "MyStudy"

Complete Example
----------------

Let's walk through a complete example:

Input File Path
^^^^^^^^^^^^^^^

Your EEG file is located at:
``/raw_data/LEMON/sub-010001/EYES_OPEN/sub-010001_task-rest_eeg.vhdr``

Rule File Setup
^^^^^^^^^^^^^^^

.. code-block:: yaml

    entities:
        task: resting
        
    non-bids:
        eeg_extension: .vhdr
        path_analysis:
            # Extract variables from the file path
            pattern: /raw_data/%study%/sub-%subject%/%condition%/sub-%subject%_task-%orig_task%_eeg.vhdr
            operation:
                # Now use the extracted variables in transformations
                entities.subject: "[subject]"                    # "010001"
                entities.session: "[condition]"                  # "EYES_OPEN" 
                entities.task: "[entities.task]"                 # "resting" (from rule file)
                entities.run: "[orig_task] + [run_suffix]"       # "rest01" (if run_suffix exists)

Variable Context During Processing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After path analysis, these variables are available:

**From path extraction:**
- ``study`` = "LEMON"
- ``subject`` = "010001"
- ``condition`` = "EYES_OPEN"
- ``orig_task`` = "rest"

**From rule file:**
- ``entities.task`` = "resting"

**After transformations:**
- ``entities.subject`` = "010001"
- ``entities.session`` = "EYES_OPEN"
- ``entities.task`` = "resting"

Real-World Examples
-------------------

Example 1: Subject ID Formatting
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Scenario**: Your files have numeric subject IDs, but you want BIDS format with "sub-" prefix.

**File path**: ``/data/participant_123/session_1/recording.eeg``

**Rule**:

.. code-block:: yaml

    non-bids:
        path_analysis:
            pattern: /data/participant_%subject_num%/session_%session_num%/recording.eeg
            operation:
                entities.subject: "sub-[subject_num]"      # Result: "sub-123"
                entities.session: "ses-[session_num]"      # Result: "ses-1"

Example 2: Task Name Standardization  
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Scenario**: Your files use inconsistent task names that need standardization.

**File path**: ``/study/S001/RestingState_EyesClosed.cnt``

**Rule**:

.. code-block:: yaml

    entities:
        task: rest  # Standard BIDS task name
        
    non-bids:
        path_analysis:
            pattern: /study/%subject%/%orig_task%.cnt
            operation:
                entities.subject: "[subject]"                    # "S001"
                entities.task: "[entities.task]"                 # "rest" (standardized)
                # Keep original for reference
                dataset_description.OriginalTask: "[orig_task]"  # "RestingState_EyesClosed"

Example 3: Complex Session Encoding
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Scenario**: Sessions are encoded with multiple pieces of information.

**File path**: ``/data/Patient001_Visit2_Baseline_Morning.edf``

**Rule**:

.. code-block:: yaml

    non-bids:
        path_analysis:
            pattern: /data/%subject%_Visit%visit%_%condition%_%time%.edf
            operation:
                entities.subject: "[subject]"                           # "Patient001"
                entities.session: "[visit] + [condition] + [time]"      # "2BaselineMorning"
                # Or with separators:
                entities.run: "[condition]_[time]"                      # "Baseline_Morning"

Example 4: Multi-part Subject IDs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Scenario**: Subject IDs have site and participant components.

**File path**: ``/study/Site_NYC_Participant_042/data.bdf``

**Rule**:

.. code-block:: yaml

    non-bids:
        path_analysis:
            pattern: /study/Site_%site%_Participant_%participant%/data.bdf
            operation:
                entities.subject: "[site] + [participant]"       # "NYC042"
                # Or keep site separate:
                entities.subject: "[participant]"               # "042"
                sidecar.Site: "[site]"                         # "NYC"

Common Patterns
---------------

String Concatenation
^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

    # Simple concatenation (no separator)
    result: "[part1] + [part2]"                    # "value1value2"
    
    # With underscore (literal underscore in the string)
    result: "[part1]_[part2]"                      # "value1_value2"
    
    # With dash
    result: "[part1]-[part2]"                      # "value1-value2"
    
    # Multiple parts
    result: "[a] + [b] + [c]"                      # "value1value2value3"

Accessing Nested Values
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

    # Access nested dictionary values with dots
    result: "[entities.task]"                      # Access entities['task']
    result: "[dataset_description.Name]"           # Access dataset_description['Name']
    result: "[sidecar.PowerLineFrequency]"         # Access sidecar['PowerLineFrequency']

Error Handling
^^^^^^^^^^^^^^

If a variable doesn't exist:

.. code-block:: yaml

    # If 'missing_var' doesn't exist in context:
    result: "[existing_var] + [missing_var]"       # Result: "value[missing_var]" (placeholder kept)

The system will log a warning and keep the placeholder, so you can identify missing variables.

Testing Your Transformations
-----------------------------

To test if your transformations work:

1. **Check the logs**: Look for transformation messages
2. **Use print_info**: Add it to raw_functions to see what's happening
3. **Start simple**: Test with basic concatenation first
4. **Check variable names**: Make sure they match your pattern exactly

.. code-block:: yaml

    non-bids:
        raw_functions:
            - print_info  # This will show you what's in the context
        path_analysis:
            operation:
                # Test with simple transformation first
                entities.subject: "[subject]"

Migration from Old eval() Syntax
---------------------------------

**Old format** (DANGEROUS - don't use):

.. code-block:: yaml

    # DON'T USE - SECURITY RISK
    non-bids:
        path_analysis:
            operation:
                entities.subject: "patterns_extracted['subject'].upper()"

**New format** (SECURE):

.. code-block:: yaml

    # USE THIS INSTEAD
    non-bids:
        path_analysis:
            operation:
                entities.subject: "[subject]"  # Simple variable reference

For complex transformations that you can't do with string concatenation, add a new function to the transformations module and submit a pull request.