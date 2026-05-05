
"""
===============================
TUI example with LEMON dataset
===============================

This example illustrates the use of ``sovabids`` on the `LEMON dataset <http://fcon_1000.projects.nitrc.org/indi/retro/MPI_LEMON.html>`_
using the terminal user interface (TUI).

A full video walkthrough is available at https://youtu.be/dOWiMTuGvAA

Install sovabids in TUI mode
-----------------------------
(`see here <https://sovabids.readthedocs.io/en/latest/README.html>`_)

.. code-block:: bash

    pip install "sovabids[tui]"

Download the LEMON dataset
---------------------------
(if you have not already done so)

.. code-block:: bash

    python -c 'from sovabids.datasets import lemon_prepare; lemon_prepare()'

This downloads the dataset to a ``_data`` subfolder inside the installed packages folder.

Launch the TUI
--------------

.. code-block:: bash

    sovatui

The TUI opens in your terminal with four tabs: **Setup**, **Rules**, **Mappings**, and **Convert**.

Tab 1 — Setup
--------------

Fill in:

* **Source directory** — path to the raw EEG files (browse with the *Browse…* button or type directly).
* **BIDS output directory** — where the converted dataset will be written.
* **Load existing rules file** (optional) — skip the Rules tab by pointing to an existing ``rules.yml``.

For the LEMON example the source path is the ``lemon`` subfolder inside ``_data``
and the BIDS path can be any empty directory you choose.

Tab 2 — Rules
--------------

Configure how files are matched and converted:

* **EEG file extension** — select ``.vhdr`` for LEMON.
* **Pattern mode** — choose *Placeholder*, *Regex*, or *File example*.
* **Path pattern** — e.g. ``%subject%_%task%.vhdr`` for placeholder mode.
* **Sidecar fields** — set power line frequency, EEG reference, etc.
* **Dataset description** — dataset name and authors.

The live preview shows how many files match the current pattern.
Use *Show all* to inspect individual files and the fields extracted from each path.
Use *Channel Names* or *Power Spectrum* to inspect the first matched file.

You can also load the existing rules file at ``examples/lemon_example_rules.yml``
via the *Load existing rules file* field in the Setup tab to skip this tab.

Tab 3 — Mappings
-----------------

Click **Generate Mappings** to get the mappings with your current setup and rules.
The table shows each source file paired with its target BIDS path.

Click **Save Mappings YAML…** to persist the mappings file to
``<bids_path>/code/sovabids/mappings.yml``.

Tab 4 — Convert
----------------

Click **Convert** to run the conversion based on the generated mappings.
Progress and log messages stream into the log panel in real time.
Errors are shown in red, warnings in yellow.

Press ``Ctrl+S`` at any time to save the current rules to
``<bids_path>/code/sovabids/rules.yml``.
Press ``Q`` to quit.
"""
