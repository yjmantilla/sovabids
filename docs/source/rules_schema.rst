Rules File Schema
=================

The rules file setups the way the conversion is done from a general point of view. It is intended to be configurable by a power-user, mainly at an institutional or organization level (or whatever level data seems to be collected uniformly). 

To make the rules file by hand we need to understand the schema of the file. For starts, the file is written in yaml. As of now the purpose of this documentation is not to teach yaml (we may have a dedicated file for that in the future). For now, you can check this `guide <https://www.cloudbees.com/blog/yaml-tutorial-everything-you-need-get-started>`_ though.

The Typical Rules File
----------------------

A typical rules file looks like this:

.. code-block:: yaml

    entities:
        task : resting
        session : ses1
    
    dataset_description :
        Name : MyDataset
        Authors :
            - Alice
            - Bob

    sidecar : 
        EEGReference : FCz
        PowerLineFrequency : 50

    channels : 
        name :
            heo : HEO
            veo : VEO
        type :
            HEO : HEOG
            VEO : VEOG

    non-bids:
        eeg_extension : .vhdr
        path_analysis:
            pattern : _data/%dataset_description.Name%/ses-%entities.session%/%entities.task%/sub-%entities.subject%.vhdr
        # code_execution: REMOVED for security reasons - use built-in transformations instead


To understand the rules file you first need to know a bit of the `bids specification for eeg <eegdocs_>`_ . Mainly that it contains 6 major files:
    - dataset_description
    - sidecar
    - channels
    - electrodes
    - coordinate system
    - events

The currently supported files are: 
    - `dataset_description <daset_descr_>`_
    - `sidecar <sidecardocs_>`_
    - `channels <chandocs_>`_
 
For each of these supported files, the yaml will have an object with its corresponding "child" properties. That is, we will have *dataset_description*, *sidecar* and *channels* objects.

Besides these objects, the yaml will have an *entities* object. Although it seems a bit obscure, *entities* is just the name the bids specification gives to the properties that affect file name structure; you can find more information of these *entities* `here <entitiesdoc_>`_ .

At last, we have the `non-bids` object which setups additional configuration that do not clearly belong to one of the previous objects.


So we will have something like this up to this point.

.. code-block:: yaml

    entities:
        something
    dataset_description:
        something
    channels:
        something
    sidecar:
        something
    non-bids:
        something


We will now delve into each of these objects.

entities
--------

The general schema of the *entities* object is:

.. code-block:: yaml

    entities:
        subject : something
        task : something
        session : something
        acquisition: something
        run : something

In essence the *entities* object holds information that triangulates the file in the study typically *subject*, *session* and *task*. Assume the *subject* is "001", the *session* is "ses1" and the *task* is "resting". The configuration will be then:

.. code-block:: yaml

    entities:
        subject : 001
        task : resting
        session : ses1

.. tip::
    In general, you only configure what you have, it is not necessary to set up empty fields.

.. warning:: 
    Notice at least a white-space separating key and value is important to avoid errors. This applies as a general principle for the rules file. That is, ``task:resting`` may give errors, so it is recommended to use ``task : resting``.

Apart from *subject*, *session* and *task*, we can have *acquisition* and *run*; refer to the `entities documentation <entitiesdoc_>`_ to know more about these two; they are setup in the same way as the previous ones.

Now, remember this file is supposed to configure general information, so one wouldn't tipically setup the *subject* in such a static way. In the *path_analysis* section of the *non-bids* object it will be explained how to infer varying properties like the *subject* directly from the path of the file.

.. warning::
    In general, you should use each of these *Rules File* objects to configure properties that apply to the dataset as a whole. The only part (for now) of the *Rules File* that allows customization in a per-file basis is the *path_analysis* functionality of the *non-bids* object.


Note that the only properties that are `obligatory <eegreq_>`_ for eeg are the *subject* and the *task*. Since the *subject* is usually inferred from the path (ie the filename), the *entities* object doesn't need that property.


.. warning::
    The *Rules File* **must** have in someway or another the `obligatory properties of the specification <eegreq_>`_.

So in the end you may end up with something like this:

.. code-block:: yaml

    entities:
        task : resting
        session : ses1

dataset_description
-------------------

The dataset description describes the dataset; you must fill it using the `properties and value formats of the given by the specification <daset_descr_>`_

As of now, we are only supporting the following info in the dataset_description object:

.. code-block:: yaml

    dataset_description:
        Name : something
        Authors : something

Suppose the dataset is named "MyDataset", and that it has two authors: "Alice" and "Bob". Then this part of the yaml will look like the following:

.. code-block:: yaml

    dataset_description :
        Name : MyDataset
        Authors :
            - Alice
            - Bob

.. note:: 

    Notice that the "BIDSVersion" (which is a REQUIRED field) is automatically set up by mne-bids, so we dont put it here in the rules.

.. warning::

    Some properties (like "Authors") are arrays of strings rather than just strings. For these fields we use the yaml list notation (``-``).


sidecar
-------

The sidecar file that accompanies eegs in the bids specification describes some technical properties of it. You can find more information `here <sidecardocs_>`_.

The currently supported schema of the sidecar object is:

.. code-block:: yaml

    sidecar : 
        EEGReference : something
        PowerLineFrequency : something

.. note::

    If you read the bids specification you may notice that the only field left that is required is the "TaskName" one. Since this is taken care by the "entities.task" object , it is not included here. The difference between the task label (*Task*) and TaskName is that the task label is obtained from the TaskName by removing non-alphanumeric characters. This idea is not currently implemented on sovabids, rather, the Task and TaskName are written as if they were the same.

The sidecar object ends up looking something like the following:

.. code-block:: yaml

    sidecar : 
        EEGReference : FCz
        PowerLineFrequency : 50


channels
--------

Channel information is mostly inferred by MNE upon reading the eeg file so usually you wouldn't need to set a rule for this. In this sense, the rules file setups whatever corrections need to be done on top of the assumptions MNE makes upon reading. 

.. tip::
    One strategy is to do the conversion without any corrections and see what was wrong, then changing the rules file accordingly.

The *channels* object currently supports the following functionality:

    * Renaming channels
    * Setting the type of channels

The schema of the *channels* object is :

.. code-block:: yaml

    channels : 
        name :
            Name : NewName
        type :
            Name : NewType

.. note::

    The types in *NewType* must correspond to the types mentioned in `the specification <chandocs_>`_ . That is: EEG EOG ECG EMG EYEGAZE GSR HEOG MISC PPG PUPIL REF RESP SYSCLOCK TEMP TRIG VEOG .

Renaming Example
^^^^^^^^^^^^^^^^

Here we rename channel "FCZ" to "FCz", and "FPZ" to "Fpz":

.. code-block:: yaml

    channels : 
        name :
            FCZ : FCz
            FPZ : Fpz

.. note::
    Notice here we are not using the list notation (``-``) of yaml; this is because of a technical reason. Internally these operations are encoded as python dictionaries rather than lists.


Type Example
^^^^^^^^^^^^

Here we give the channel "heo" the type "HEOG" and the channel "veo" the type "VEOG".

.. code-block:: yaml

    channels : 
        type :
            heo : HEOG
            veo : VEOG

Renaming and Typing simultaniously:

It is possible that we need to change the name and the type of a channel. In that case only to refer to such channel as the *OldName* in the *name* part of the *channels* object. In the other parts use the *NewName*.

To illustrate the procedure, suppose we want to rename "veo" to "VEO" , "heo" to "HEO" and also set their types to "VEOG" and "HEOG" respecitively. You would do then:

.. code-block:: yaml

    channels : 
        name :
            heo : HEO
            veo : VEO
        type :
            HEO : HEOG
            VEO : VEOG



non-bids
--------

This is the most complex object. As of now what is supported is:

.. code-block:: yaml

    non-bids :
        eeg_extension : something
        path_analysis : 
            something
        code_execution :
            something

eeg_extension
^^^^^^^^^^^^^

This property just defines the extension of the eeg files we want to read. If this property is non-existent then the eeg files will be any from the following extensions: ['.set' ,'.cnt' ,'.vhdr' ,'.bdf' ,'.fif']. 

.. note::
    Notice it is preferable that you put the dot before the extension; the code should add it if you dont though.

Supposing you are using brainvision files, then you would configure it as:

.. code-block:: yaml

    non-bids :
        eeg_extension : '.vhdr'

path_analysis
^^^^^^^^^^^^^

Is used to infer information from the path. Any of the fields from the previous objects are supported as long they consist of a single simple value (anything that is a single number or string). The pattern is applied to every file that has the *eeg_extension* mentioned before.

There are 3 ways to do the *path_analysis*, by a *regex pattern* , by a *placeholder pattern*, or by *paired example*.


regex pattern
"""""""""""""

For this you will need to know regex. Mainly you need to set a capture group for each property you want to infer from the path. You will also need to set the properties you want to infer through a list.

The schema we want to arrive at is :

.. code-block:: yaml
    
    non-bids:
        path_analysis:
            pattern : regex-pattern
            fields :
                - field1
                - field2


This will be explained better with an example, suppose you want to extract information from the following file path: 

.. code-block:: text

    Y:\code\sovabids\_data\lemon\ses-001\resting\sub-010002.vhdr

Intuitively you identify the following pattern: 

.. code-block:: text

    some useless path\ dataset name \ ses-session \ task \ sub- subject.vhdr


You associate each of the properties you want to extract to the properties of the *Rules File*. That is:

    * dataset name is dataset_description.Name
    * session is entities.session
    * task is entities.task
    * subject is entities.subject

These have to be written in a property called *fields* and in the order as they appear in the regex pattern (from left to right).


.. note::

    Notice sovabids uses dot notation to nest properties. That is ```field1.field2`` means that we get inside ``field1`` and then inside ``field2``.

Now you make your regex using capture groups and the forward-slash as the path separator. In this case it would suffice to use: 

.. code-block:: text
    
    _data\/(.+)\/ses-(.+)\/(.+)\/sub-(.+).vhdr

.. tip::
    The capture group (.+) is recommended. The dot will match any character (except line terminators) and the plus sign will match it 1 to unlimited times. Basically it will try to match the longest strings it can given the pattern you gave.

.. warning::
    We need to escape the forward slash in the regex pattern so ``/`` becomes ``\/``.

So your *path_analysis* object is wrote in the *Rules File* as:

.. code-block:: yaml
    
    non-bids:
        path_analysis:
            pattern : _data\/(.+)\/ses-(.+)\/(.+)\/sub-(.+).vhdr
            fields :
                - dataset_description.Name
                - entities.session
                - entities.task
                - entities.subject

.. warning::

    Use the forward-slash as the path separator (``/``) in your path strings regardless of the symbol your OS uses. This is to avoid problems when reading strings. This applies to all of the modes of *path_analysis* :
    regex patterns, placeholder patterns and paired example.

.. warning::
    If the value extracted from a field includes hyphens or underscores (-,_) they will be deleted from the value so as to accomodate automatically to the bids standard.
    The only way to bypass this is if the field is "ignore" (without the quotations).

placeholder pattern
"""""""""""""""""""

The placeholder pattern is intended for less technical users as it is more intuitive (but less powerful) than regex. Internally it is regex nevertheless. Mainly we just need to pass a pattern that mimics the structure of the files by using placeholders to indicate what fields are there.

The schema we want to arrive at is :

.. code-block:: yaml
    
    non-bids:
        path_analysis:
            pattern : placeholder-pattern


The placeholder functionality is inspired by the mp3tag software feature of "format strings":

.. image:: https://user-images.githubusercontent.com/36543115/122836377-c15edd80-d2b7-11eb-8c95-7c5c294e112b.gif

Using the same example as before, suppose you want to extract information from the following file path: 

.. code-block:: text

    Y:\code\sovabids\_data\lemon\ses-001\resting\sub-010002.vhdr

Again, you identify the following pattern: 

.. code-block:: text

    some useless path\ dataset name \ ses-session \ task \ sub- subject.vhdr


You associate each of the properties you want to extract to the properties of the *Rules File* as done before. That is:

    * dataset name is dataset_description.Name
    * session is entities.session
    * task is entities.task
    * subject is entities.subject

Now you just need to set the pattern, remember we need to use forward-slash notation:

.. code-block:: text
    
    _data/%dataset_description.Name%/ses-%entities.session%/%entities.task%/sub-%entities.subject%.vhdr

.. note::
    Notice that the differences are: 
        * that we enclose the desired fields between percentages.
        * that the fields are already in the pattern string
        * that there is no need to escape the forward-slash (```/``) character

.. tip::

    You can use %ignore% if that part of the pattern varies but you don't care about its value.

.. warning::
    If the value extracted from a field includes hyphens or underscores (-,_) they will be deleted from the value so as to accomodate automatically to the bids standard.
    The only way to bypass this is if the field is "ignore".

The placeholder has two advanced configurations which define how the pattern is translated to a regex pattern:

.. code-block:: yaml
    
    non-bids:
        path_analysis:
            pattern : placeholder-pattern
            matcher :  something
            encloser : something

The matcher is the regex string that replaces the fields in the placeholder pattern. By default is ``(.+)``

The encloser is the character that encloses the fields. By default is ``%``.

So if you don't set up these configurations, it is equivalent to having:

.. code-block:: yaml
    
    non-bids:
        path_analysis:
            pattern : placeholder-pattern
            matcher :  (.+)
            encloser : "%"


What we need to write in the *Rules File* is then:

.. code-block:: yaml
    
    non-bids:
        path_analysis:
            pattern : _data/%dataset_description.Name%/ses-%entities.session%/%entities.task%/sub-%entities.subject%.vhdr

.. tip::

    You don't need to put the whole path structure, just from where it interests you. In the examples here we are only interested from the ``_data`` folder.

.. warning::

    It is advisable to include the folder just before the one that is of interest to you. This is so that the sofware is able to discriminate what is of interest in the first field. In this example we started from ``_data`` although in reality we are interested is in the next folder (``lemon``). If we do ``%dataset_description.Name%/ses-%entities.session%/%entities.task%/sub-%entities.subject%.vhdr`` (this is the same pattern but without the ``_data`` folder), the software will have trouble distinguishing what is of interest at the start of the string. This warning applies both to regex and placeholder patterns.


paired example (EXPERIMENTAL)
""""""""""""""""""""""""""""""

.. warning::
    
    This feature is experimental, is not well tested so it may not run correctly.

This is the easiest way to use the *path_analysis* functionality. The idea is to provide a *(source,target)* example.

The *source* would be the filepath of any of the files you want to convert.

The *target* would be the filepath of where you expect the file to go following the bids standard.

The schema we want to arrive at is :

.. code-block:: yaml
    
    non-bids:
        path_analysis:
            source: source_path example
            target: target_path example

This will be explained better with an example, suppose this is the source filepath example you want to use: 

.. code-block:: text

    data/lemon/V001/resting/010002.vhdr

You fabricate by yourself where do you want it to go following the bids standard:

.. code-block:: text

    data_bids/sub-010002/ses-001/eeg/sub-010002_ses-001_task-resting_eeg.vhdr

Sovabids will try to infer the pattern from this example.

So your *path_analysis* object is wrote in the *Rules File* as:

.. code-block:: yaml
    
    non-bids:
        path_analysis:
            source : data/lemon/V001/resting/010002.vhdr
            target : data_bids/sub-010002/ses-001/eeg/sub-010002_ses-001_task-resting_eeg.vhdr

.. warning::

    Notice that we expect you to input a valid bids file as a target. That means the target you provide does follow the bids standard.


.. warning::

    Examples and ambiguity:


    Notice the provided (source,target) pair is not ambiguous. This means that the values for each bids entity only appear once in the provided strings.

    An example of an ambiguous pair would be:

    .. code-block:: text

        source='data/lemon/session001/taskT001/010002.vhdr'
        target='data_bids/sub-010002/ses-001/eeg/sub-010002_ses-001_task-T001_eeg.vhdr'

    Here session '001' is contained inside task 'T001' so sovabids has trouble finding the pattern.

    sovabids developers are planning to include the possibility of giving a list of (source,target) pairs to resolve ambiguity automatically.
    But for now, this is not yet included.

    Do note that the (source,target) example pair is fictional, you can give a non-ambiguous example you imagined by yourself. It does not have to be a real file.

    Following the previous ambiguous example:

    .. code-block:: text

        source='data/lemon/session001/taskT001/010002.vhdr'
        target='data_bids/sub-010002/ses-001/eeg/sub-010002_ses-001_task-T001_eeg.vhdr'


    You could give the following fictional non-ambiguous example: 

    .. code-block:: text

        source='data/lemon/session009/taskT001/010002.vhdr'
        target='data_bids/sub-010002/ses-009/eeg/sub-010002_ses-009_task-T001_eeg.vhdr'
    
    Where since 009 is not found in any other part of the string, it is non ambiguous.
    
    The session 009 may not actually exist on the dataset but for our purposes that does not matter.
    We just care about finding a naming pattern here.

operation (EXPERIMENTAL)
""""""""""""""""""""""""""""

.. warning::
    
    This feature is experimental, is not well tested so it may not run correctly.

This is an advance feature for weird cases where an operation between fields extract by pattern matching is necessary to produce a single bids field.

For example, it is common to have subject grouping with numbering per subject, such as:

    .. code-block:: text

        Healthy_01_EyesOpen.set
        Healthy_02_EyesOpen.set
        Control_01_EyesOpen.set
        Control_02_EyesOpen.set

Lets says the result you want for subject Healthy-01 is:

    .. code-block:: text

        entities.subject = Healthy01
        entities.task = EyesOpen

To do this an operation procedure is introduced in the yaml as follows:

.. code-block:: yaml
    
    non-bids:
        path_analysis:
            pattern : %a%_%b%_%entities.task%.set
            operation :
                entities.subject : "[a] + [b]"

As you may notice, this introduces "field intermediaries" that we can operate on using python expressions.

The field intermediaries you use should be alphanumeric strings, 1 or 2 characters long.

Note that to express the operation needed you need to enclose the intermediary field within [].

The fields you can use are any of those you define by placeholder or regex beforehand, as long as they dont have dots.

You could express the configuration mentioned before using regex with:

.. code-block:: yaml
    
    non-bids:
        path_analysis:
            pattern : (.+)_(.+)_(.+).set
            fields :
                - a
                - b
                - entities.task
            operation :
                entities.subject : "[a] + [b]"


output_format (EXPERIMENTAL)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. warning::
    
    This feature is experimental, is not well tested so it may not run correctly.


Sets up the output format by controlling the *format* parameter of *mne_bids.write_raw_bids*. Acceptable values are the ones supported by that function (currently 'auto' | 'BrainVision' | 'EDF' | 'FIF').

.. code-block:: yaml
    
    non-bids:
        output_format: 'BrainVision'

file_filter (EXPERIMENTAL)
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. warning::
    
    This feature is experimental, is not well tested so it may not run correctly.

Used to ignore or only include certain files when sovabids is scanning the **source_path**.

The schema of this property is:

.. code-block:: yaml
    
    non-bids:
        file_filter:
            - include : regex string to use for inclusion
            - exclude : regex string to use for exclusion

This will be executed in the order of appearance. You may include various include/exclude stages. For example, if you have these files:

.. code-block:: bash

    01_eyesClosed.set
    01_eyesClosed_PREP_preprocessed.set
    01_eyesClosed_highpass.set
    01_eyesOpen.set
    01_eyesOpen_PREP_preprocessed.set
    01_eyesOpen_highpass.set
    02_eyesClosed.set
    02_eyesClosed_PREP_preprocessed.set
    02_eyesClosed_highpass.set
    02_eyesOpen.set
    02_eyesOpen_PREP_preprocessed.set
    02_eyesOpen_highpass.set
    03_eyesClosed.set
    03_eyesClosed_PREP_preprocessed.set
    03_eyesClosed_highpass.set
    03_eyesOpen.set
    03_eyesOpen_PREP_preprocessed.set
    03_eyesOpen_highpass.set

If you want to only convert raw eyesClosed files, you could use:

.. code-block:: yaml

    non-bids:
        file_filter:
            - include : eyesClosed
            - exclude : _PREP
            - exclude : _highpass


code_execution (DEPRECATED - SECURITY RISK)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. danger::

    **This feature has been removed for security reasons.**
    
    The ``code_execution`` functionality allowed arbitrary Python code execution, which posed significant security risks including:
    
    - Remote code execution through malicious rule files
    - System compromise and data exfiltration
    - Privilege escalation attacks
    
    **Migration:** Use built-in transformation functions instead. Contact maintainers if you need specific functionality that was previously implemented through code execution.

**Migration to Secure Alternatives:**

Use the new secure transformation system instead:

1. **For string operations in path analysis:**

   .. code-block:: yaml
   
       non-bids:
           path_analysis:
               operation:
                   entities.subject: "[a] + [b]"  # String concatenation
                   entities.session: "[prefix]_[session_num]"

2. **For raw object processing:**

   .. code-block:: yaml
   
       non-bids:
           raw_functions:
               - print_info              # Print raw object information
               - drop_bad_channels       # Remove bad channels
               - filter_line_noise_50hz  # Apply 50Hz notch filter
               - resample_500hz          # Resample to 500Hz

**Available Built-in Functions:**

- ``print_info``: Print information about the raw object
- ``drop_bad_channels``: Drop channels marked as bad
- ``set_montage_standard_1020``: Set standard 10-20 montage
- ``filter_line_noise_50hz``: Apply 50Hz notch filter
- ``filter_line_noise_60hz``: Apply 60Hz notch filter  
- ``resample_500hz``: Resample data to 500Hz
- ``crop_to_10min``: Crop recording to first 10 minutes

**Extending Functionality:**

To add custom functions, fork the repository and add new functions to ``sovabids/transformations.py``:

.. code-block:: python

    @register_raw_function("my_custom_function")
    def my_custom_function(raw: BaseRaw) -> BaseRaw:
        \"\"\"Your custom processing function.\"\"\"
        # Your safe processing code here
        return raw

The complete non-bids object
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Finally, we will have this *non-bids* object (if using the placeholder pattern option):

.. code-block:: yaml

    non-bids:
        eeg_extension : .vhdr
        path_analysis:
            pattern : _data/%dataset_description.Name%/ses-%entities.session%/%entities.task%/sub-%entities.subject%.vhdr
            operation:
                entities.subject: "[subject_prefix] + [subject_num]"  # String concatenation example
        raw_functions:
            - print_info              # Print raw object info
            - drop_bad_channels       # Remove bad channels  
            - filter_line_noise_50hz  # Apply 50Hz notch filter
        file_filter:
            - include : eyesClosed
            - exclude : _PREP
            - exclude : _highpass
        output_format: 'BrainVision'


.. _entitiesdoc: https://bids-specification.readthedocs.io/en/stable/99-appendices/09-entities.html

.. _eegreq: https://github.com/bids-standard/bids-specification/blob/master/src/schema/datatypes/eeg.yaml

..  _daset_descr: https://bids-specification.readthedocs.io/en/stable/03-modality-agnostic-files.html#dataset-description

.. _sidecardocs: https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/03-electroencephalography.html#sidecar-json-_eegjson

.. _chandocs: https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/03-electroencephalography.html#channels-description-_channelstsv

.. _eegdocs: https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/03-electroencephalography.html