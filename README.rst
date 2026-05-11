.. image:: https://img.shields.io/codecov/c/github/yjmantilla/sovabids
   :target: https://app.codecov.io/gh/yjmantilla/sovabids
   :alt: codecov

.. image:: https://img.shields.io/github/actions/workflow/status/yjmantilla/sovabids/python-tests.yml?branch=main&label=tests
   :target: https://github.com/yjmantilla/sovabids/actions?query=workflow%3Apython-tests
   :alt: Python tests

.. image:: https://readthedocs.org/projects/sovabids/badge/?version=latest
   :target: https://sovabids.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://img.shields.io/badge/Preprint-Zenodo-orange
  :target: https://doi.org/10.5281/zenodo.10292410

sovabids
========

`Visit the documentation <https://sovabids.readthedocs.io/>`_

.. after-init-label

* sovabids is a python package for automating EEG to BIDS conversion (experimental MEG support).

* **New to sovabids?** Start with the `Quickstart guide <https://sovabids.readthedocs.io/en/latest/quickstart.html>`_.

* sovabids can be used through (click to see the examples):
   a. `its python API <https://sovabids.readthedocs.io/en/latest/auto_examples/lemon_example.html#using-the-python-api>`_
   b. `its CLI entry points <https://sovabids.readthedocs.io/en/latest/auto_examples/lemon_example.html#using-the-cli-tool>`_
   c. `its terminal user interface (TUI) <https://youtu.be/dOWiMTuGvAA>`_
   d. `its JSON-RPC entry points (needs a server running the backend) <https://sovabids.readthedocs.io/en/latest/auto_examples/rpc_example.html>`_
   e. `its minimal web-app GUI <https://sovabids.readthedocs.io/en/latest/auto_examples/gui_example.html>`_

.. note::

   The advantage of the JSON-RPC way is that it can be used from other programming languages. 
   
   Limitation:
   
   Do notice that at the moment the files have to be on the same computer that runs the server.

.. warning::

   MEG support is **experimental**. sovabids correctly routes MEG data to the ``meg`` BIDS datatype,
   but does not expose MEG-specific metadata requirements such as empty-room recordings,
   manufacturer calibration files, or digitization coordinate systems. For complex MEG datasets
   (Elekta/Neuromag, CTF, KIT) those steps must be handled manually after conversion using
   MNE-BIDS directly — see the `MNE-BIDS MEG conversion guide <https://mne.tools/mne-bids/stable/auto_examples/convert_mne_sample.html>`_.
   The output format is automatically set to FIF for MEG data; you do not need to set
   ``non-bids.output_format`` manually (but you may still override it if needed).

.. _supported-formats:

Supported Formats
-----------------

sovabids reads EEG files via `MNE-Python's read_raw <https://mne.tools/stable/generated/mne.io.read_raw.html>`_,
which supports a wide range of formats including BrainVision, EDF/BDF, EEGLAB, FIF, CNT, KIT/SQD, CTF, and more.
See the full list in the MNE documentation.

Output is always written as a valid BIDS dataset. The table below lists formats that can also be
**exported natively** (i.e., the BIDS data files stay in that format rather than being converted to BrainVision):

.. list-table::
   :header-rows: 1
   :widths: 20 15 20 30

   * - Format
     - Extension
     - Extra needed
     - Notes
   * - BrainVision
     - ``.vhdr``
     - *(core)*
     - Default output format; ``pybv`` included in base install
   * - EDF
     - ``.edf``
     - ``sovabids[formats]``
     - Requires ``edfio``; date must be in 1985–2084
   * - EEGLAB
     - ``.set``
     - ``sovabids[formats]``
     - Requires ``eeglabio``; montage with fiducials needed
   * - FIF
     - ``.fif``
     - *(core)*
     - MNE native format; use for MEG data (experimental — see warning above)

Install export support for EDF and EEGLAB::

   pip install "sovabids[formats]"

For all other readable formats, sovabids converts the data to BrainVision on output (the default mne-bids behaviour).

.. tip::

   sovabids supports incremental conversion: files whose BIDS output already exists are skipped
   automatically, so you can safely re-run after adding new participants without re-converting
   the whole dataset. To force a full re-conversion, delete the output folder and start over.
   The Python API returns ``{'succeeded': [...], 'skipped': [...], 'failed': [...]}`` so you
   can distinguish newly converted files, skipped files, and failures. Skips are also logged
   at ``WARNING`` level so they appear in CLI output without ``-v``.

Architecture
------------

The main elements of sovabids are:
    * A source path with the original dataset.
    * A bids path that will be the output path of the conversion.
    * A rules file that configures how the conversion is done from the general perspective.
    * A mapping file that encodes how the conversion is performed to each individual file of the dataset.

.. image:: https://mermaid.ink/svg/eyJjb2RlIjoiZ3JhcGggTFJcbiAgICBTPlwiU291cmNlIHBhdGhcIl1cbiAgICBCPlwiQmlkcyBwYXRoXCJdXG4gICAgUj5cIlJ1bGVzIGZpbGVcIl1cbiAgICBBUigoXCJBcHBseSBSdWxlc1wiKSlcbiAgICBNPlwiTWFwcGluZ3MgZmlsZVwiXVxuICAgIENUKChcIkNvbnZlcnQgVGhlbVwiKSlcbiAgICBPWyhcIkNvbnZlcnRlZCBkYXRhc2V0XCIpXVxuICAgIFMgLS0-IEFSXG4gICAgQiAtLT4gQVJcbiAgICBSIC0tPiBBUlxuICAgIEFSIC0tPiBNXG4gICAgTSAtLT4gQ1RcbiAgICBDVCAtLT4gT1xuICAiLCJtZXJtYWlkIjp7InRoZW1lIjoiZm9yZXN0In0sInVwZGF0ZUVkaXRvciI6ZmFsc2UsImF1dG9TeW5jIjp0cnVlLCJ1cGRhdGVEaWFncmFtIjpmYWxzZX0

Internally sovabids uses `MNE-Python <https://github.com/mne-tools/mne-python>`_ and `MNE-BIDS <https://github.com/mne-tools/mne-bids>`_ to perform the conversion. In a sense is a wrapper that allows to do conversions from the command line.


Basic Usage
-----------


Terminal User Interface (sovatui)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The easiest way to use sovabids is through its terminal user interface (TUI) called sovatui. This will allow you to do the conversion without having to write any command line code, and also to have a more visual experience of the conversion process. The TUI guides you through the full conversion workflow in four tabs: Setup, Rules, Mappings, and Convert.


Installation for TUI usage
--------------------------

This will install sovabids with the terminal user interface dependencies.

.. code-block:: bash

   pip install "sovabids[tui]"

Running the TUI
----------------

.. code-block:: bash

   sovatui

See the `TUI tutorial video <https://youtu.be/dOWiMTuGvAA>`_ for a walkthrough and its `example <https://sovabids.readthedocs.io/en/latest/auto_examples/tui_example.html>`_.

Command Line Interface (CLI) entry-points
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


Use sovabids through its CLI entry-points as follows:

Installation
""""""""""""

.. code-block:: bash

   pip install sovabids


sovapply
""""""""

Use the sovapply entry-point to produce a mapping file from a source path, an output bids root path and a rules filepath.


.. code-block:: bash

   sovapply source_path bids_path rules_path

By default the mapping file made will have the following filepath:

.. code-block:: text

   bids_path/code/sovabids/mappings.yml


sovaconvert
"""""""""""

Use the sovaconvert entry-point to convert the dataset given its mapping file.

.. code-block:: bash

   sovaconvert mapping_file


Using the experimental web GUI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Installation for WEB GUI usage
------------------------------

This will install sovabids for usage with an experimental web gui.

.. code-block:: bash

   pip install "sovabids[gui]"

See the `WEB GUI tutorial video <https://youtu.be/PW84cy6uUJs>`_ for a walkthrough and its `example <https://sovabids.readthedocs.io/en/latest/auto_examples/gui_example.html>`_.


Using the experimental bidscoin plugin
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


For the experimental bidscoin plugin, install the sovabids fork of bidscoin manually:

.. code-block:: bash

   pip install "git+https://github.com/yjmantilla/bidscoin.git@sovabids"

Follow the example at https://sovabids.readthedocs.io/en/latest/auto_examples/bidscoin_example.html to see how to use the plugin.


Installation for developers
---------------------------

Fork this repo and run:

.. code-block:: bash

   git clone https://github.com/<gh-username>/sovabids.git
   cd sovabids
   pip install -e ".[dev]"


Funding
-------

.. image:: https://developers.google.com/open-source/gsoc/resources/downloads/GSoC-logo-horizontal.svg
   :width: 250px
   :alt: Google Summer of Code

.. image:: https://user-images.githubusercontent.com/4021595/119062104-3caf4400-ba19-11eb-8211-e2e9ce831a16.png
   :width: 250px
   :alt: Funding logo



Acknowledgments
---------------

sovabids is developed with the help of the following entities:

.. image:: https://www.neurodesk.org/static/docs/overview/uq_logo.png
   :width: 250px
   :alt: University of Queensland

.. image:: https://www.neurodesk.org/static/docs/overview/swinburne_uni_logo.png
   :width: 250px
   :alt: Swinburne University

.. image:: https://www.udea.edu.co/wps/wcm/connect/udea/2288a382-341c-41ee-9633-702a83d5ad2b/logosimbolo-horizontal-png.png?MOD=AJPERES&CVID=ljeSAX9
   :width: 250px
   :alt: Universidad de Antioquia

.. image:: https://www.udea.edu.co/wps/wcm/connect/udea/eba017e2-87fb-40c7-b7d8-6bb7d0e008ae/Logo_GRUNECO_R.jpg?MOD=AJPERES&CACHEID=ROOTWORKSPACE.Z18_L8L8H8C0LODDC0A6SSS2AD2GO4-eba017e2-87fb-40c7-b7d8-6bb7d0e008ae-l-x54eU
   :width: 250px
   :alt: GRUNECO

.. image:: https://www.neurodesk.org/static/docs/overview/nif.png
   :width: 250px
   :alt: Neuroimaging Facility

.. image:: https://www.incf.org/sites/default/files/INCF_logo_with_tagline.png
   :width: 250px
   :alt: INCF



Academic Works
---------------

* `Poster for the Big Data Neuroscience Workshop 2022 (Austin, Texas) <https://canva.link/n96b5zngko5hdrg>`_

* `Poster for OHBM 2022 Anual Meeting <https://canva.link/i4dunn18hm8mezk>`_

* `Video for OHBM 2022 Anual Meeting <https://youtu.be/7M7JLrl6KAk>`_

* `Poster for the eResearch Australasia Conference 2021 <https://canva.link/00tfwmoi7idsoud>`_



What does sova means?
---------------------

sova is a contraction of 'eso va' which mean 'that goes' in spanish.

Nevertheless the real usage by the original developers is just to convey the idea of :

   we will make it happen, we dont know how, but we will
