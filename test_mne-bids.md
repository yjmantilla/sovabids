# MNE-BIDS TEST

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

## Download Example Dataset
```
cd /home/neuro
mkdir lemon
cd lemon
curl --remote-name https://fcp-indi.s3.amazonaws.com/data/Projects/INDI/MPI-LEMON/Compressed_tar/EEG_MPILMBB_LEMON/EEG_Raw_BIDS_ID/sub-032301.tar.gz

curl --remote-name https://fcp-indi.s3.amazonaws.com/data/Projects/INDI/MPI-LEMON/Compressed_tar/EEG_MPILMBB_LEMON/EEG_Raw_BIDS_ID/sub-032302.tar.gz

curl --remote-name https://fcp-indi.s3.amazonaws.com/data/Projects/INDI/MPI-LEMON/Compressed_tar/EEG_MPILMBB_LEMON/EEG_Raw_BIDS_ID/sub-032303.tar.gz

curl --remote-name https://fcp-indi.s3.amazonaws.com/data/Projects/INDI/MPI-LEMON/name_match.csv
```

## Clone Repository
```bash
git clone https://github.com/yjmantilla/sovabids.git
cd sovabids
```

## Prepare Example

Decompresses the dataset and fixes a filename inconsistency (without this correction the file won't be able to be opened in mne)

Run lemon_prepary.py

## Perform Conversion

As of now is just a basic conversion. Not much metadata added, besides what is already inferred by mne.

Run test_mne-bids.py