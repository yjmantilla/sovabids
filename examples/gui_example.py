  
"""
===============================
GUI example with LEMON dataset 
===============================

This example illustrates the use of ``sovabids`` on the `LEMON dataset <http://fcon_1000.projects.nitrc.org/indi/retro/MPI_LEMON.html>`_
using both the preliminary GUI tool.

* Install Sovabids in advanced-usage mode (`see here <https://sovabids.readthedocs.io/en/latest/README.html#installation-for-advanced-usage>`_)

* Download the Lemon dataset if you have not already done so.

.. code-block:: bash

    python -c 'from sovabids.datasets import lemon_prepare; lemon_prepare()'

This will download the lemon dataset inside the '_data' subfolder of the cloned sovabids repository.

* Run front/app/app.py in a terminal (the front folder is the one in the root of the cloned sovabids repository.)

In example, run:

.. code-block:: bash
    python front/app/app.py


* Go to your browser at http://127.0.0.1:5000/ , you will see

.. image:: https://github.com/yjmantilla/sovabids/raw/main/docs/source/_static/front_1_intro.png

This is an introductory page of the GUI.

* Click Upload Files

.. image:: https://github.com/yjmantilla/sovabids/raw/main/docs/source/_static/front_2_click_upload.png

* Choose Files

Click 'Choose Files', select the lemon folder (inside the _data subdirectory) and click submit.

.. image:: https://github.com/yjmantilla/sovabids/raw/main/docs/source/_static/front_3_upload.png

You will need to wait while the files are copied to the server. Since these are heavy eegs, it will take a bit.

* Deselect any files you want to skip:

.. image:: https://github.com/yjmantilla/sovabids/raw/main/docs/source/_static/front_4_deselect.png

Here we won't skip any files. Notice though that there are non-eeg files (.csv and tar.gz ) mixed in there. Sovabids will skipp them automatically.

Click Send.

* Confirm detected eegs.

Sovabids will show the individual eegs found. Notice that since this is a brainvision dataset, sovabids lists the main files of this format (the .vhdr files) since the other ones (.eeg and .vmrk) are sidecars.

.. image:: https://github.com/yjmantilla/sovabids/raw/main/docs/source/_static/front_5_detected.png


* The rules files

A suitable rules file is already at examples/lemon_example_rules.yml, you can upload that one.

Click Choose File, then in the popup window select the rules file, click open and then submit.

.. image:: https://github.com/yjmantilla/sovabids/raw/main/docs/source/_static/front_6_upload_rules.png

After that you will notice the text pane is updated:

.. image:: https://github.com/yjmantilla/sovabids/raw/main/docs/source/_static/front_7_inspect_rules.png

You can edit the rules directly, as shown here where we modify the dataset name to "Modified Name'.

.. image:: https://github.com/yjmantilla/sovabids/raw/main/docs/source/_static/front_8_edit_rules.png

Once ready, scroll down to find another submit and click it to continue.

.. image:: https://github.com/yjmantilla/sovabids/raw/main/docs/source/_static/front_9_submit_rules.png


* Edit individual mappings

You will now see a list of the eeg files, for each you can edit its mapping. At first you will see an empty text pane since no eeg file is chosen.

.. image:: https://github.com/yjmantilla/sovabids/raw/main/docs/source/_static/front_10_mappings.png

Click any of the files for editing it:

.. image:: https://github.com/yjmantilla/sovabids/raw/main/docs/source/_static/front_11_select_mapping.png

Once clicked, you will see the corresponding mapping:

.. image:: https://github.com/yjmantilla/sovabids/raw/main/docs/source/_static/front_12_the_mapping.png

You can edit the INDIVIDUAL mapping of this file, in example here we will change the power line frequency of this eeg to 60 Hz.

.. image:: https://github.com/yjmantilla/sovabids/raw/main/docs/source/_static/front_13_edit_mapping.png

To save the edited individual mapping, press Send at the right:

.. image:: https://github.com/yjmantilla/sovabids/raw/main/docs/source/_static/front_14_save_mapping.png

You will be redirected to the empty mapping, but if you click the same eeg file again you will notice the changes are saved:

.. image:: https://github.com/yjmantilla/sovabids/raw/main/docs/source/_static/front_15_check_mapping.png

Once the mappings are ready, click next:

.. image:: https://github.com/yjmantilla/sovabids/raw/main/docs/source/_static/front_16_mappings_ready.png


* Proceed to the conversion

Click on the button:

.. image:: https://github.com/yjmantilla/sovabids/raw/main/docs/source/_static/front_17_conversion_click.png

Once clicked it will take a while before the program finishes (a feedback information of the progress is not yet implemented on this preliminary GUI).

* Save your conversion

When the files are ready you will see:

.. image:: https://github.com/yjmantilla/sovabids/raw/main/docs/source/_static/front_18_download_click.png

Once you click there, sovabids will begin compressing your files so it will take a bit until the download windows is shown. Select where you want to download the file and press save.

.. image:: https://github.com/yjmantilla/sovabids/raw/main/docs/source/_static/front_19_download_popup.png

When the download is ready, navigate to the chosen folder and decompress the files. Go into the correspondent folder to see the converted files:

.. image:: https://github.com/yjmantilla/sovabids/raw/main/docs/source/_static/front_20_converted_files.png

* Inspect the sovabids logs and mappings

Inside the code/sovabids subdirectory you will see the mappings and log files.

.. image:: https://github.com/yjmantilla/sovabids/raw/main/docs/source/_static/front_21_sovabids_files.png

The mappings.yml file will hold the mappings:

.. image:: https://github.com/yjmantilla/sovabids/raw/main/docs/source/_static/front_22_mapping_file.png

The logs will hold run-time information of the procedure:

.. image:: https://github.com/yjmantilla/sovabids/raw/main/docs/source/_static/front_23_log_files.png

"""