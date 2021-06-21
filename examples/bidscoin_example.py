from bidscoin.plugins.sova2coin import is_eeg,is_sourcefile,get_eegfield,get_attribute,bidsmapper_plugin
from pathlib import Path
from bidscoin.bidscoiner import bidscoiner,bidsmapper
from bidscoin.bids import load_bidsmap
from bidscoin.bidscoin import lsdirs
p = Path(r"Y:\code\sovabids\_data\lemon2\sub-010003\ses-001\resting\sub-010003.vhdr")
pnot = Path(r"Y:\code\sovabids\_data\lemon2\sub-010003\ses-001\resting\sub-010003.eeg")

assert is_sourcefile(p)=='EEG'
assert is_sourcefile(pnot)==''
assert get_eegfield('sidecar.SamplingFrequency',p) == 2500.0
assert get_attribute('EEG',p,'sidecar.SamplingFrequency') == 2500.0

session_path = Path(r"Y:\code\sovabids\_data\lemon2\sub-010003")
lsdirs(session_path)
folder = session_path
wildcard='*'
[fname for fname in sorted(folder.glob(wildcard)) if fname.is_dir() and not fname.name.startswith('.')]

templatefile = Path(r'Y:\code\bidscoin\bidscoin\heuristics\bidsmap_sovabids.yaml')
template, _              = load_bidsmap(templatefile)


#bidsmapper_plugin(session=session_path, bidsmap_new=template, bidsmap_old={}, template=template, store=True)


#bidsmapper Y:\code\sovabids\_data\lemon2\ Y:\code\sovabids\_data\lemon2_bids -t bidsmap_sovabids

#bidscoiner -f Y:\code\sovabids\_data\lemon2\ Y:\code\sovabids\_data\lemon2_bids
bidsmapper(rawfolder='Y:/code/sovabids/_data/lemon2/',bidsfolder='Y:/code/sovabids/_data/lemon2_bids',templatefile= 'bidsmap_sovabids')

bidscoiner(rawfolder    = 'Y:/code/sovabids/_data/lemon2/',
            bidsfolder   = 'Y:/code/sovabids/_data/lemon2_bids',just_wrap=True)