# MNE-BIDS EXAMPLE

## Install miniconda
```bash
curl -o the_miniconda_installer.sh https://repo.anaconda.com/miniconda/Miniconda3-py39_4.9.2-Linux-x86_64.sh
chmod +x the_miniconda_installer.sh
./the_miniconda_installer.sh
```

close and reopen terminal

## Install MNE
```bash
curl --remote-name https://raw.githubusercontent.com/mne-tools/mne-python/main/environment.yml
conda env update --file environment.yml
pip install --user -U mne-bids[full]
```

## Clone Repository
```bash
git clone https://github.com/yjmantilla/sovabids.git
cd sovabids
pip install .
```

## Prepare Example

Downloads and decompresses the dataset,also fixes a filename inconsistency (without this correction the file won't be able to be opened in mne)

Run lemon_prepare.py

## Perform Conversion

As of now is just a basic conversion. Not much metadata added, besides what is already inferred by mne.

Run test_mne-bids.py
