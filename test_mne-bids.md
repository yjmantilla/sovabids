# MNE-BIDS TEST

```
curl -o the_miniconda_installer.sh https://repo.anaconda.com/miniconda/Miniconda3-py39_4.9.2-Linux-x86_64.sh
chmod +x the_miniconda_installer.sh
./the_miniconda_installer.sh
```

close and reopen terminal

```
curl --remote-name https://raw.githubusercontent.com/mne-tools/mne-python/main/environment.yml
conda env update --file environment.yml
pip install --user -U mne-bids[full]
```