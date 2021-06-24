import mne
import numpy as np
from mne_bids.write import _write_raw_brainvision
from sovabids.utils import create_dir
import os

PATTERN = '%dataset%/%task%/%session%/sub%subject%_%run%'
DATASET = 'DUMMY'
NSUBS = 11
NTASKS = 2
NRUNS = 2
NSESSIONS = 4
NCHANNELS = 32
SFREQ = 200 # hz
STOP = 10 # in sec
NUMEVENTS = 10


this_dir = os.path.dirname(__file__)
data_dir = os.path.abspath(os.path.join(this_dir,'..','_data'))
create_dir(data_dir)


def get_num_leading_zeros(N):
    return int(np.floor(np.log10(N-1)))

sub_zeros = get_num_leading_zeros(NSUBS)
subs = [str(x).zfill(sub_zeros+1) for x in range(NSUBS)]

task_zeros = get_num_leading_zeros(NTASKS)
tasks = [ 'T'+str(x).zfill(task_zeros+1) for x in range(NTASKS)]

run_zeros = get_num_leading_zeros(NRUNS)
runs = [ str(x).zfill(run_zeros+1) for x in range(NRUNS)]

ses_zeros = get_num_leading_zeros(NSESSIONS)
sessions = [ 'S'+str(x).zfill(ses_zeros+1) for x in range(NSESSIONS)]


# Create some dummy metadata
n_channels = NCHANNELS
sampling_freq = SFREQ  # in Hertz
info = mne.create_info(n_channels, sfreq=sampling_freq)

times = np.linspace(0, STOP, STOP*sampling_freq, endpoint=False)
data = np.zeros((NCHANNELS,times.shape[0]))

raw = mne.io.RawArray(data, info)

new_events = mne.make_fixed_length_events(raw, duration=STOP//NUMEVENTS)

for task in tasks:
    for session in sessions:
        for run in runs:
            for sub in subs:
                dummy = PATTERN.replace('%dataset%',DATASET)
                dummy = dummy.replace('%task%',task)
                dummy = dummy.replace('%session%',session)
                dummy = dummy.replace('%subject%',sub)
                dummy = dummy.replace('%run%',run)
                path = [data_dir] +dummy.split('/')
                fpath = os.path.join(*path)
                _write_raw_brainvision(raw,fpath,new_events)