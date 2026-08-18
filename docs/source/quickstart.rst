Quickstart
==========

This page walks through a full EEG-to-BIDS conversion in one place.
The four steps are always the same regardless of which interface you use:

.. contents:: Steps
   :local:
   :depth: 1
   :class: this-will-duplicate-information-and-it-is-still-useful-here

Step 1 — Install
----------------

Install sovabids (this gives you the command-line tools and the Python API):

.. code-block:: bash

   pip install sovabids

The terminal user interface (TUI) is an optional, experimental extra:

.. code-block:: bash

   pip install "sovabids[tui]"

.. tip::
   sovabids can read any EEG format supported by MNE's ``read_raw``. For native EDF or EEGLAB output,
   install ``pip install "sovabids[formats]"``. MEG support is experimental — see the
   :ref:`Supported Formats <supported-formats>` section in the README for details and caveats.

Step 2 — Prepare a rules file
------------------------------

The **rules file** tells sovabids how to interpret your dataset as a whole —
which file extension to look for, how to extract subject/session/task from file
paths, power line frequency, channel corrections, and so on.

See the full :doc:`rules_schema` for all options.

A minimal example for a BrainVision dataset where subject is encoded in the filename:

.. literalinclude:: ../../examples/quickstart_rules.yml
   :language: yaml

Save this as ``rules.yml``.

.. note::
   The ``pattern`` value is wrapped in quotes because it begins with ``%``. YAML reserves ``%`` as an
   indicator character, so a plain (unquoted) scalar cannot start with it — any ``pattern`` that begins
   with ``%`` (for example one starting with ``%ignore%``) must be quoted, e.g.
   ``pattern: "%ignore%/sub-%entities.subject%.vhdr"``.

.. tip::
   If you use the TUI (``sovatui``), the Rules tab builds this file for you
   interactively — no hand-editing required.
   See the `TUI tutorial video <https://youtu.be/dOWiMTuGvAA>`_ for a walkthrough.

Step 3 — Generate mappings
---------------------------

The **mappings file** is produced by applying your rules to every file in the
source directory. It encodes the per-file source → target conversion plan.

See the full :doc:`mappings_schema` to understand the output format.

**Using the CLI**:

.. code-block:: bash

   sovapply source_path bids_path rules.yml

This writes the mappings file to:

.. code-block:: text

   bids_path/code/sovabids/mappings.yml

**Using the Python API**:

.. code-block:: python

   from sovabids.rules import apply_rules
   mappings = apply_rules(source_path, bids_path, rules="rules.yml")

**Using the TUI** (experimental):

.. code-block:: bash

   sovatui

Open the *Mappings* tab and click **Generate Mappings**. Inspect the
source → target pairs, then click **Save Mappings YAML** if you want to keep
a copy.

Step 4 — Convert
-----------------

Apply the mappings to produce the BIDS dataset.

**Using the CLI**:

.. code-block:: bash

   sovaconvert bids_path/code/sovabids/mappings.yml

**Using the Python API**:

.. code-block:: python

   from sovabids.convert import convert_them
   result = convert_them(mappings)
   print(result["succeeded"])  # newly converted source paths
   print(result["skipped"])    # paths skipped because BIDS output already existed
   print(result["failed"])     # paths that raised an error

**Using the TUI** (experimental):

Open the *Convert* tab and click **Convert**. Logs stream in real time.

The converted dataset will be at ``bids_path``. The CLI exits with a non-zero
status code if any files failed, making it suitable for use in scripts and CI pipelines.

.. tip::
   **Incremental conversion**: files whose BIDS output already exists are skipped
   automatically. Re-running after adding new participants converts only the new files.
   To force a full re-conversion, delete the output folder and start over.

Next steps
----------

* Full worked example (Python API + CLI): `LEMON dataset example <https://sovabids.readthedocs.io/en/latest/auto_examples/lemon_example.html>`_
* Full worked example (TUI): `TUI example <https://sovabids.readthedocs.io/en/latest/auto_examples/tui_example.html>`_
* Rules file reference: :doc:`rules_schema`
* Mappings file reference: :doc:`mappings_schema`
* Python API reference: :doc:`autoapi/index`
