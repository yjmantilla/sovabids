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

* sovabids is a python package for automating eeg2bids conversion. 

* sovabids can be used through (click to see the examples): 
   a. `its python API <https://sovabids.readthedocs.io/en/latest/auto_examples/lemon_example.html#using-the-python-api>`_ 
   b. `its CLI entry points <https://sovabids.readthedocs.io/en/latest/auto_examples/lemon_example.html#using-the-cli-tool>`_
   c. `its JSON-RPC entry points (needs a server running the backend) <https://sovabids.readthedocs.io/en/latest/auto_examples/rpc_example.html>`_
   d. `its minimal web-app GUI <https://sovabids.readthedocs.io/en/latest/auto_examples/gui_example.html>`_

.. note::

   The advantage of the JSON-RPC way is that it can be used from other programming languages. 
   
   Limitation:
   
   Do notice that at the moment the files have to be on the same computer that runs the server.

.. warning::

   Currently meg2bids conversion is not supported, but this is a targeted feature.

.. danger::

   **Security Update**: Code execution functionality has been removed for security reasons. 
   See the `Security Notice <https://sovabids.readthedocs.io/en/latest/security_notice.html>`_ for details and migration guidance.

.. tip::

   By default sovabids will skip files already converted. If you want to overwrite previous conversions currently you need to delete the output folder (by yourself) and start sovabids over again.

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
   pip install -r requirements-user.txt

Installation for GUI usage
-------------------------------

This will install sovabids for usage with an experimental web gui, and as an experimental plugin for bidscoin.

.. code-block:: bash

   git clone https://github.com/yjmantilla/sovabids.git
   cd sovabids
   pip install -r requirements-gui.txt


Installation for developers
---------------------------

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

Funding
-------

.. raw:: html

   <br/>
   <img src="https://developers.google.com/open-source/gsoc/resources/downloads/GSoC-logo-horizontal.svg" width="250">
   <br/>
   <img src="https://user-images.githubusercontent.com/4021595/119062104-3caf4400-ba19-11eb-8211-e2e9ce831a16.png" width="250">



Acknowledgments
---------------

sovabids is developed with the help of the following entities:

.. raw:: html

   <br/>
   <img src="https://www.neurodesk.org/static/docs/overview/uq_logo.png" width="250">
   <br/>
   <img src="https://www.neurodesk.org/static/docs/overview/swinburne_uni_logo.png" width="250">
   <br/>
   <img src="https://www.udea.edu.co/wps/wcm/connect/udea/2288a382-341c-41ee-9633-702a83d5ad2b/logosimbolo-horizontal-png.png?MOD=AJPERES&CVID=ljeSAX9" width="250">
   <br/>
   <img src="https://www.udea.edu.co/wps/wcm/connect/udea/eba017e2-87fb-40c7-b7d8-6bb7d0e008ae/Logo_GRUNECO_R.jpg?MOD=AJPERES&CACHEID=ROOTWORKSPACE.Z18_L8L8H8C0LODDC0A6SSS2AD2GO4-eba017e2-87fb-40c7-b7d8-6bb7d0e008ae-l-x54eU" width="250">
   <br/>
   <img src="https://www.neurodesk.org/static/docs/overview/nif.png" width="250">
   <br/>
   <img src="https://www.incf.org/sites/default/files/INCF_logo_with_tagline.png" width="250">



Academic Works
---------------

* `Poster for the Big Data Neuroscience Workshop 2022 (Austin, Texas) <https://www.canva.com/design/DAFMDNgVuGU/UTEbbAYk0JG0d-JpdjQOQg/view?utm_content=DAFMDNgVuGU&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton>`_

* `Poster for OHBM 2022 Anual Meeting <https://www.canva.com/design/DAFBHD1bCs4/FNZLtwC78ip_5jt7bcAajw/view?utm_content=DAFBHD1bCs4&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton>`_

* `Video for OHBM 2022 Anual Meeting <https://youtu.be/7M7JLrl6KAk>`_

* `Poster for the eResearch Australasia Conference 2021 <https://www.canva.com/design/DAErO4bo4uk/gnHqwkVFs2qP7U1FhlViVQ/view?utm_content=DAErO4bo4uk&utm_campaign=designshare&utm_medium=link&utm_source=publishsharelink>`_



What does sova means?
---------------------

sova is a contraction of 'eso va' which mean 'that goes' in spanish.

Nevertheless the real usage by the original developers is just to convey the idea of :

   we will make it happen, we dont know how, but we will
