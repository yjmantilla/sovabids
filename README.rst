.. image:: https://img.shields.io/codecov/c/github/yjmantilla/sovabids
   :target: https://app.codecov.io/gh/yjmantilla/sovabids
   :alt: codecov

.. image:: https://img.shields.io/github/workflow/status/yjmantilla/sovabids/python-tests/main?label=tests
   :target: https://github.com/yjmantilla/sovabids/actions?query=workflow%3Apython-tests
   :alt: Python tests

.. image:: https://readthedocs.org/projects/sovabids/badge/?version=latest
   :target: https://sovabids.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

sovabids
========

`Visit the documentation <https://sovabids.readthedocs.io/>`_

.. after-init-label

* sovabids is a python package for automating eeg2bids conversion. 

* sovabids can be used through its python API or through its cli entry points.

Architecture
------------

The main elements of sovabids are:
    * A source path with the original dataset.
    * A bids path that will be the output path of the conversion.
    * A rules file that configures how the conversion is done from the general perspective.
    * A mapping file that encodes how the conversion is performed to each individual file of the dataset.

.. image:: https://mermaid.ink/svg/eyJjb2RlIjoiZ3JhcGggTFJcbiAgICBTPlwiU291cmNlIHBhdGhcIl1cbiAgICBCPlwiQmlkcyBwYXRoXCJdXG4gICAgUj5cIlJ1bGVzIGZpbGVcIl1cbiAgICBBUigoXCJBcHBseSBSdWxlc1wiKSlcbiAgICBNPlwiTWFwcGluZ3MgZmlsZVwiXVxuICAgIENUKChcIkNvbnZlcnQgVGhlbVwiKSlcbiAgICBPWyhcIkNvbnZlcnRlZCBkYXRhc2V0XCIpXVxuICAgIFMgLS0-IEFSXG4gICAgQiAtLT4gQVJcbiAgICBSIC0tPiBBUlxuICAgIEFSIC0tPiBNXG4gICAgTSAtLT4gQ1RcbiAgICBDVCAtLT4gT1xuICAiLCJtZXJtYWlkIjp7InRoZW1lIjoiZm9yZXN0In0sInVwZGF0ZUVkaXRvciI6ZmFsc2UsImF1dG9TeW5jIjp0cnVlLCJ1cGRhdGVEaWFncmFtIjpmYWxzZX0

Internally sovabids uses `MNE-Python <https://github.com/mne-tools/mne-python>`_ and `MNE-BIDS <https://github.com/mne-tools/mne-bids>`_ to perform the conversion. In a sense is a wrapper that allows to do conversions from the command line.

Installation
------------

.. code-block:: bash

   git clone https://github.com/yjmantilla/sovabids.git
   cd sovabids
   pip install .

Installation for development
----------------------------

Fork this repo and run:

.. code-block:: bash

   git clone https://github.com/<gh-username>/sovabids.git
   cd sovabids
   pip install -r requirements-dev.txt

Notice  that the requirements-dev.txt file already has the sovabids installation using editable mode.


Basic Usage
-----------

The easiest way is to use sovabids through its CLI entry-points as follows:

sovapply
^^^^^^^^

Use the sovapply entry-point to produce a mapping file from a source path, an output bids root path and a rules filepath.


.. code-block:: bash

   sovapply source_path bids_path rules_path

By default the mapping file made will have the following filepath:

.. code-block:: text

   bids_path/code/sovabids/mappings.yml


sovaconvert
^^^^^^^^^^^

Use the sovaconvert entry-point to convert the dataset given its mapping file.

.. code-block:: bash

   sovaconvert mapping_file


Acknowledgments
---------------

sovabids is developed with the help of the following entities:

.. raw:: html

   <br/>
   <img src="https://raw.githubusercontent.com/NeuroDesk/vnm/master/uq_logo.png" width="250">
   <br/>
   <img src="https://raw.githubusercontent.com/NeuroDesk/vnm/master/logo-long-full.svg" width="250">
   <br/>
   <img src="https://www.udea.edu.co/wps/wcm/connect/udea/2288a382-341c-41ee-9633-702a83d5ad2b/logosimbolo-horizontal-png.png?MOD=AJPERES&CVID=ljeSAX9" width="250">
   <br/>
   <img src="https://www.udea.edu.co/wps/wcm/connect/udea/eba017e2-87fb-40c7-b7d8-6bb7d0e008ae/Logo_GRUNECO_R.jpg?MOD=AJPERES&CACHEID=ROOTWORKSPACE.Z18_L8L8H8C0LODDC0A6SSS2AD2GO4-eba017e2-87fb-40c7-b7d8-6bb7d0e008ae-l-x54eU" width="250">
   <br/>
   <img src="https://github.com/NeuroDesk/vnm/blob/master/nif.png" width="250">
