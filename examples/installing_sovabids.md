# Installing SOVABIDS

## Install miniconda (Optional)

```bash
curl -o the_miniconda_installer.sh https://repo.anaconda.com/miniconda/Miniconda3-py39_4.9.2-Linux-x86_64.sh
chmod +x the_miniconda_installer.sh
./the_miniconda_installer.sh
```

close and reopen terminal

assure conda is on path

```bash
$HOME/miniconda3/bin/conda init
```

## Install MNE-BIDS

Linux:

```bash
curl --remote-name https://raw.githubusercontent.com/mne-tools/mne-python/main/environment.yml
conda env update --file environment.yml
pip install --user -U mne-bids[full]
```

Windows via pip:

```bash
pip install --user -U mne-bids[full]
pip install --user -U mne
```

windows via Conda:

```bash
conda install --channel conda-forge --no-deps mne-bids
```

## Clone Repository and install sovabids

```bash
git clone https://github.com/yjmantilla/sovabids.git
conda activate mne
cd sovabids
pip install .
```
