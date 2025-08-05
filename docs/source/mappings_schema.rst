Mappings File Schema
====================

The **Mappings File** setups the way the conversion is done from an individual point of view, that is, in a per-file basis. It is intended to be produced by the **apply_rules** (in the cli **sovapply**) module, or by a GUI editor that allows the user to edit the mapping in a per-file basis.

The **Mappings File** is in yaml format. As of now the purpose of this documentation is not to teach yaml (we may have a dedicated file for that in the future). For now, you can check this `guide <https://www.cloudbees.com/blog/yaml-tutorial-everything-you-need-get-started>`_ though.

The Typical Mapping File
------------------------

A typical mapping file looks like this:

.. code-block:: yaml


    General:
    IO:
        source: Y:\code\sovabids\_data\DUMMY\DUMMY_SOURCE
        target: Y:\code\sovabids\_data\DUMMY\DUMMY_BIDS_custom
    channels:
        name:
        '0': ECG_CHAN
        '1': EOG_CHAN
        type:
        ECG_CHAN: ECG
        EOG_CHAN: EOG
    dataset_description:
        Authors:
        - A1
        - A2
        Name: Dummy
    non-bids:
        # code_execution: REMOVED for security reasons - use built-in transformations instead
        eeg_extension: .vhdr
        path_analysis:
        pattern: T%entities.task%/S%entities.session%/sub%entities.subject%_%entities.acquisition%_%entities.run%.vhdr
    sidecar:
        EEGReference: FCz
        PowerLineFrequency: 50
        SoftwareFilters:
        Anti-aliasing filter:
            Roll-off: 6dB/Octave
            half-amplitude cutoff (Hz): 500
    Individual:
    - IO:
        source: Y:\code\sovabids\_data\DUMMY\DUMMY_SOURCE\T0\S0\sub0_0_0.vhdr
        target: Y:\code\sovabids\_data\DUMMY\DUMMY_BIDS_custom\sub-0\ses-0\eeg\sub-0_ses-0_task-0_acq-0_run-0_eeg.vhdr
    channels:
        name:
        '0': ECG_CHAN
        '1': EOG_CHAN
        type:
        ECG_CHAN: ECG
        EOG_CHAN: EOG
    dataset_description:
        Authors:
        - A1
        - A2
        Name: Dummy
    entities:
        acquisition: '0'
        run: '0'
        session: '0'
        subject: '0'
        task: '0'
    non-bids:
        # code_execution: REMOVED for security reasons - use built-in transformations instead
        eeg_extension: .vhdr
        path_analysis:
        pattern: T%entities.task%/S%entities.session%/sub%entities.subject%_%entities.acquisition%_%entities.run%.vhdr
    sidecar:
        EEGReference: FCz
        PowerLineFrequency: 50
        SoftwareFilters:
        Anti-aliasing filter:
            Roll-off: 6dB/Octave
            half-amplitude cutoff (Hz): 500
    - IO:
        source: Y:\code\sovabids\_data\DUMMY\DUMMY_SOURCE\T0\S0\sub0_0_1.vhdr
        target: Y:\code\sovabids\_data\DUMMY\DUMMY_BIDS_custom\sub-0\ses-0\eeg\sub-0_ses-0_task-0_acq-0_run-1_eeg.vhdr
    channels:
        name:
        '0': ECG_CHAN
        '1': EOG_CHAN
        type:
        ECG_CHAN: ECG
        EOG_CHAN: EOG
    dataset_description:
        Authors:
        - A1
        - A2
        Name: Dummy
    entities:
        acquisition: '0'
        run: '1'
        session: '0'
        subject: '0'
        task: '0'
    non-bids:
        # code_execution: REMOVED for security reasons - use built-in transformations instead
        eeg_extension: .vhdr
        path_analysis:
        pattern: T%entities.task%/S%entities.session%/sub%entities.subject%_%entities.acquisition%_%entities.run%.vhdr
    sidecar:
        EEGReference: FCz
        PowerLineFrequency: 50
        SoftwareFilters:
        Anti-aliasing filter:
            Roll-off: 6dB/Octave
            half-amplitude cutoff (Hz): 500


Relation to the Rules File
--------------------------

As you may have noticed, the **Mappings File** has a lot of similiraties with the **Rules File**. This is because the **Mappings File** is just the rules after being applied to each file.


The General and Invididual Objects
----------------------------------

Essentially, the mappings file will have a **General** and an **Invididual** object at the top level.

The **General** object will contain a copy of the "general" rules; the **Individual** object will hold rules for each of the files to be converted. That is, each file holds "a copy" of the rules along with the modifications that apply to that particular file.

.. code-block:: yaml

    General :
        rules
    Individual :
        list of rules


In the example shown above you may notice that the **General** object does not have an **entities** object, thats because the **entities** object was inferred from the **path_analysis** rule.
Nevertheless, the **Individual** object does show the entities object . That is because the **entities** object was filled by applying the **path_analysis** rule.

.. note::

    As of now, the only object that actually shows the result of applying the rules is the **entities** object. The other ones will just show the rule applied to that particular file.

The Individual object as a list
-------------------------------

An important difference between the **General** object and the **Individual** object is that the **General** object holds a single set of rules, whereas the **Individual** object maintains a list of them; in other words, one set of rules for each file. As a result of this, the **Individual** object will be a list; that why it has a (``-``) at the start of every mapping it holds:

.. code-block:: yaml

    General :
        rules
    Individual :
        - rules for file 1
        - rules for file 2
        ...
        - rules for file N

THE IO object
-------------

A difference you will notice between the **Rules File** and the **Mappings File** is the **IO** object.

This object just holds input/output information, or more specifically, the **source** and **target**.

IO in the General object
^^^^^^^^^^^^^^^^^^^^^^^^

For the **General** object we will have :

.. code-block:: yaml

    General:
    IO:
        source: source path - root folder of the data to be converted (input)
        target: target path - root folder of the bids directory (output)


IO in the Invididual object
^^^^^^^^^^^^^^^^^^^^^^^^^^^

For one of the elements of the **Invididual** object we will have :

.. code-block:: yaml

    Individual:
    IO:
        source: source filepath - non-bids input data to be converted
        target: target filepath - bids output of that file

Conclusions
-----------

In essence, the **Mappings File** is just the **Rules File** copied once for each file, plus one more to have the "General" perspective. The copies of the rules made for each file will also hold any modification of the rules that apply for that particular file. 

The **IO** object just holds input/output information from the point-of-view of files.