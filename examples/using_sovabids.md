# Using SOVABIDS

## Install sovabids

See the corresponding doc example (docs\installing_sovabids.md)

## Prepare Example

For this example we will be using a few files from the following [dataset](http://fcon_1000.projects.nitrc.org/indi/retro/MPI_LEMON.html).

We have to download and decompress the dataset. We also need to fix a filename inconsistency (without this correction the file won't be able to be opened in mne). Luckily all of that is done by the lemon_prepare.py script.

Run examples/lemon_prepare.py

```bash
python ./examples/lemon_prepare.py
```

## Perform Conversion

As of now is just a basic conversion. Not much metadata added, besides what is already inferred by mne.

Run /examples/sovabids_example.py

```bash
python ./examples/sovabids_example.py
```

## Understanding the code

First we import the modules needed; from sovabids we will just need ``apply_rules`` which is a function that gets a source path, a target path and a set of rules to perform the conversion. The idea is that in the target path you will get the desired bids output.

```python
import os
import shutil
from sovabids.rules import apply_rules
```

We will now define the variables needed for the ``apply_rules`` function. Because this example is intended to run relative to the repository directory we use relative path but for real use-cases it is easier to just input the absolute-path.

In the end:

- source_path=_data\lemon
- bids_root=_data\lemon_bids
- rules_path=examples\sovabids_example_rules.yml

Doing this with the ``os.path.join function`` allows us to not worry about the particular OS one is testing the code in.

```python
this_dir = os.path.dirname(__file__)
data_dir = os.path.join(this_dir,'..','_data')
data_dir = os.path.abspath(data_dir)

source_path = os.path.abspath(os.path.join(data_dir,'lemon'))
bids_root= os.path.abspath(os.path.join(data_dir,'lemon_bids'))
rules_path = os.path.join('examples','sovabids_examples_rules.yml')
```

We will clean the output path as a safety measure from previous conversions.

```python
#CLEAN BIDS PATH
try:
    shutil.rmtree(bids_root)
except:
    pass
```

And now we just apply our function:

```python
apply_rules(source_path,bids_root,rules_path)
```

## Understanding the rules file

The most important and complicated part of this is making the rules file, either by hand or by the "DISCOVER_RULES" module (which is not yet implemented).

To do it by hand we need to understand the schema of the file. For starts, the file is written in yaml. As of now the purpose of this file is not to teach yaml (we may have a dedicated file for that in the future). You can check this [link](https://www.cloudbees.com/blog/yaml-tutorial-everything-you-need-get-started) though.

The bids eeg specification sets up mainly 6 files:

- dataset_description
- sidecar file for eeg
- channels
- electrodes
- coordinate system
- events

So for each of these files we will have a dictionary which configures the file.

We will also have an "entities" dictionary which holds information that triangulates the file in the study (subject,session,task,acquisition,run). Is called entities just because bids call them that way but the name could be changed.

Along with the 7 dictionaries already mentioned we will have a last one which holds non-bids information, that is, is not directly related to a bids file.

So in total we have 8 dictionaries, with names shorted to a single word:

- entities
- dataset_description
- sidecar
- channels
- electrodes
- coordsystem
- events
- non-bids

### General and Single Rules files

The following file will apply properties to all EEGs so its info is general. So whatever information you put here has to be general. In the future we will have an individual/single rules files.

We will now get into each dictionary:

### Entities

It can hold the following information which is self-explanatory. For more info read [this](https://bids-specification.readthedocs.io/en/latest/02-common-principles.html)

```yaml
entities : 
  subject : val
  session : val
  task : val
  acquisition : val
  run : val
```

For this example we dont need session,acquisition nor run. The task is constant for all subjects (resting). Now, the subject key holds the label of the subject. Since this varies from subject to subject we won't set that value as general. How we will do it then? you may ask... Well, we will infer that from the filename in the non-bids dictionary. So in the end we will just set the task information in this dictionary.

```yaml
entities : 
  task : resting
```

Notice the indentation. Each level are 2 spaces here.

### Dataset Description

As of now, we are only supporting the following info in this dictionary:

```yaml
dataset_description :
  Name : val
  Authors : val
```

Note that "BIDSVersion" which is a REQUIRED field is automatically set up by mne-bids, so we dont put it here in the rules.

By seeing the dataset [link](http://fcon_1000.projects.nitrc.org/indi/retro/MPI_LEMON.html) we can get the authors and a candidate name for it. We will just call this dataset as "Lemon".

You can write that info directly in yaml; remember how to do a list in this format (the ``-``).

```yaml
dataset_description:
  Name : Lemon
  Authors:
    - Anahit Babayan
    - Miray Erbey
    - Deniz Kumral
    - Janis D. Reinelt
    - Andrea M. F. Reiter
    - Josefin Röbbig
    - H. Lina Schaare
    - Marie Uhlig
    - Alfred Anwander
    - Pierre-Louis Bazin
    - Annette Horstmann
    - Leonie Lampe
    - Vadim V. Nikulin
    - Hadas Okon-Singer
    - Sven Preusser
    - André Pampel
    - Christiane S. Rohr
    - Julia Sacher1
    - Angelika Thöne-Otto
    - Sabrina Trapp
    - Till Nierhaus
    - Denise Altmann
    - Katrin Arelin
    - Maria Blöchl
    - Edith Bongartz
    - Patric Breig
    - Elena Cesnaite
    - Sufang Chen
    - Roberto Cozatl
    - Saskia Czerwonatis
    - Gabriele Dambrauskaite
    - Maria Dreyer
    - Jessica Enders
    - Melina Engelhardt
    - Marie Michele Fischer
    - Norman Forschack
    - Johannes Golchert
    - Laura Golz
    - C. Alexandrina Guran
    - Susanna Hedrich
    - Nicole Hentschel
    - Daria I. Hoffmann
    - Julia M. Huntenburg
    - Rebecca Jost
    - Anna Kosatschek
    - Stella Kunzendorf
    - Hannah Lammers
    - Mark E. Lauckner
    - Keyvan Mahjoory
    - Natacha Mendes
    - Ramona Menger
    - Enzo Morino
    - Karina Näthe
    - Jennifer Neubauer
    - Handan Noyan
    - Sabine Oligschläger
    - Patricia Panczyszyn-Trzewik
    - Dorothee Poehlchen
    - Nadine Putzke
    - Sabrina Roski
    - Marie-Catherine Schaller
    - Anja Schieferbein
    - Benito Schlaak
    - Hanna Maria Schmidt
    - Robert Schmidt
    - Anne Schrimpf
    - Sylvia Stasch
    - Maria Voss
    - Anett Wiedemann
    - Daniel S. Margulies
    - Michael Gaebler
    - Arno Villringer
```

Notice again the indentation.

### Sidecar

What currently is supported is:

```yaml
sidecar : 
  EEGReference : val
  PowerLineFrequency : val
```

If you know about bids you may notice that the only field left that is required is the "TaskName" one. Since this is taken care by the "entities" dictionary, we didn't include it on this dictionary.

This information is trickier to get. The reference is "FCz" according to [this paper](https://www.nature.com/articles/sdata2018308).

The power line noise is 50Hz since this data was recorded in Europe, you may also know this from the spectrum plot. So we have:

```yaml
sidecar : 
  PowerLineFrequency : 50
  EEGReference : FCz #https://www.nature.com/articles/sdata2018308
```

Notice you can comment stuff with ``#`` in yaml. That is useful for configuration files.

### Channels

Channel information is mostly inferred by MNE upon reading the file so usually you wouldn't need to set a rule for this. As of now what is supported is setting the type of the channels since that is the field most prone to be wrong.

```yaml
channels :
  type : 
    chan_label : chan_type
```

In our case all channel types are correctly inferred by mne but one. An ocular. We will overwrite this mistake with the correct type as follows:

```yaml
channels:
  type :
    VEOG : VEOG
```

Here we are assigning the channel labeled as "VEOG" with the type "EOG". The types have to follow the [BIDS notation](https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/03-electroencephalography.html).

| Keyword  | Description                                                  |
|----------|--------------------------------------------------------------|
| AUDIO    | Audio signal                                                 |
| EEG      | Electroencephalogram channel                                 |
| EOG      | Generic electrooculogram (eye), different from HEOG and VEOG |
| ECG      | Electrocardiogram (heart)                                    |
| EMG      | Electromyogram (muscle)                                      |
| EYEGAZE  | Eye tracker gaze                                             |
| GSR      | Galvanic skin response                                       |
| HEOG     | Horizontal EOG (eye)                                         |
| MISC     | Miscellaneous                                                |
| PPG      | Photoplethysmography                                         |
| PUPIL    | Eye tracker pupil diameter                                   |
| REF      | Reference channel                                            |
| RESP     | Respiration                                                  |
| SYSCLOCK | System time showing elapsed time since trial started         |
| TEMP     | Temperature                                                  |
| TRIG     | System triggers                                              |
| VEOG     | Vertical EOG (eye)                                           |

Notice here we only set up the type of a single channel, that is because all the other ones are inferred correctly as "EEG" by mne. You are free to set the type of each channel here by hand though; it would overwrite the types gotten by MNE.

For example you could do:

```yaml
channels:
  type :
    VEOG : VEOG
    F3 : EEG
```

Notice here we are not using the list notation (``-``) of yaml; this is because of a technical reason.

### non-bids

This is the hardest dictionary to master. As of now what is supported is:

```yaml
non-bids :
  eeg_extension : value
  path_analysis : 
    pattern : value
  code_execution : code
```

#### eeg_extension

Just defines the extension of the eeg files we want to read, it could also not be in the dictionary, in which case the eeg files will be any from the following extensions: ['.set' ,'.cnt' ,'.vhdr' ,'.bdf' ,'.fif']. Notice it is preferable that you put the dot before the extension; the code should add it if you dont though.

#### path_analysis

Is used to infer information from the path. Any of the fields from the previous dictionaries are supported as long they consist of a single simple value (anything that is a single number or string). The pattern is applied to every file that has the eeg_extension mentioned before.

How it works? You put the pattern you know beforehand of the filepath. The "pattern" is just writing the path of any eeg file on the source path and replacing the part which holds information with ``%dictionary.field%``. The name of the field are the ones on this schema; that is, to set the dataset name you could use ``%dataset_description.Name%``. Notice the dot notation is used to get inside the dictionaries.

You don't need to put the whole absolute path if you are just interested in the filename which is the case in this example. You could see the ``tests/test_path_parser.py`` for examples with absolute paths. The folders of the path pattern should be separated by thr forward slash (``/``). With backward slash it should work but errors could arise.

Every file on our source dataset has this name: sub-XXXXXX.vhdr, where XXXXXX is the subject label. So we will set up our pattern_path to: ``sub-%entities.subject%.vhdr``. You can also infer many fields at once but the fields are required to be separated by at least a character:

```yaml
good: %entities.subject%-%entities.task%
bad: %entities.subject%%entities.task%
```

Notice that here we are depending on the extension being the same, what if the extension varied?. For cases like this you can use a special field "ignore" (``%ignore%``). The algorithm will throw away that information. Remember though that we need the fields to be separated by at least a character; luckily the extension is always preceded by a dot. So you could do ``sub-%entities.subject%.%ignore%``.

#### code_execution

Is used to hold a list of commands you want to run for additional flexibility but at the cost of knowing a bit about the backend of this package. Mainly that eeg object is called "raw" and is from mne; that is, you can manipulate it if you know how to use mne.

In this example we will just call ``print(raw.info)``, this doesnt do anything interesting besides printing stuff on the console.

#### Final non-bids section

Wow, this part was intense but in the end we just have:

```yaml
non-bids:
  eeg_extension : .vhdr
  path_analysis:
    pattern : sub-%entities.subject%.vhdr
  code_execution: # To manipulate the raw mne object for further changes
    - print(raw.info)
```

### Other dictionaries

The following dictionaries are not yet supported:

- electrodes
- coordsystem
- events

This is because our priority is to have first the REQUIRED fields of BIDS. They will be done in the future.

## The whole yaml file

The whole yaml file can be found in examples\sovabids_example_rules.yml , but here is it anyway:

```yaml
entities:
  task : resting
dataset_description:
  Name : Lemon
  Authors:
    - Anahit Babayan
    - Miray Erbey
    - Deniz Kumral
    - Janis D. Reinelt
    - Andrea M. F. Reiter
    - Josefin Röbbig
    - H. Lina Schaare
    - Marie Uhlig
    - Alfred Anwander
    - Pierre-Louis Bazin
    - Annette Horstmann
    - Leonie Lampe
    - Vadim V. Nikulin
    - Hadas Okon-Singer
    - Sven Preusser
    - André Pampel
    - Christiane S. Rohr
    - Julia Sacher1
    - Angelika Thöne-Otto
    - Sabrina Trapp
    - Till Nierhaus
    - Denise Altmann
    - Katrin Arelin
    - Maria Blöchl
    - Edith Bongartz
    - Patric Breig
    - Elena Cesnaite
    - Sufang Chen
    - Roberto Cozatl
    - Saskia Czerwonatis
    - Gabriele Dambrauskaite
    - Maria Dreyer
    - Jessica Enders
    - Melina Engelhardt
    - Marie Michele Fischer
    - Norman Forschack
    - Johannes Golchert
    - Laura Golz
    - C. Alexandrina Guran
    - Susanna Hedrich
    - Nicole Hentschel
    - Daria I. Hoffmann
    - Julia M. Huntenburg
    - Rebecca Jost
    - Anna Kosatschek
    - Stella Kunzendorf
    - Hannah Lammers
    - Mark E. Lauckner
    - Keyvan Mahjoory
    - Natacha Mendes
    - Ramona Menger
    - Enzo Morino
    - Karina Näthe
    - Jennifer Neubauer
    - Handan Noyan
    - Sabine Oligschläger
    - Patricia Panczyszyn-Trzewik
    - Dorothee Poehlchen
    - Nadine Putzke
    - Sabrina Roski
    - Marie-Catherine Schaller
    - Anja Schieferbein
    - Benito Schlaak
    - Hanna Maria Schmidt
    - Robert Schmidt
    - Anne Schrimpf
    - Sylvia Stasch
    - Maria Voss
    - Anett Wiedemann
    - Daniel S. Margulies
    - Michael Gaebler
    - Arno Villringer
sidecar:
  PowerLineFrequency : 50
  EEGReference : FCz #https://www.nature.com/articles/sdata2018308

channels:
  type : # To overwrite channel types inferred by MNE
    VEOG : eog #white-space separating key and value is important

non-bids:
  eeg_extension : .vhdr
  path_analysis :
    pattern : sub-%entities.subject%.vhdr
  code_execution: # To manipulate the raw mne object for further changes
    - print(raw.info)
```

## Validation

You should now be able to upload the dataset to assert if it is a valid bids dataset:

![validation](2021-06-16-04-44-27.png)

## CLI USAGE

SOVABIDS has command line entry points so you can do:

```bash
sovapply sourcefolder outputfolder rulesfile
```

Or in our case:

```bash
sovapply y:\code\sovabids\_data\lemon y:\code\sovabids\_data\lemon_bids y:\code\sovabids\examples\sovabids_example_rules.yml
```

## Blueprint of the schema

The overall blueprint of the Rules File is in sovabids\rules_schema.yml .

## Future Work

...
