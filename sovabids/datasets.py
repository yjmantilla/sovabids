"""Module with dataset utilities.
"""
import os
from pandas import read_csv
import shutil
from sovabids.files import download,_get_files
from sovabids.misc import get_num_digits
from sovabids.parsers import parse_from_regex
import mne
import numpy as np
from mne_bids.write import _write_raw_brainvision

def lemon_prepare():
    """Download and prepare a few files of the LEMON dataset.

    Notes
    -----

    See the `LEMON dataset <http://fcon_1000.projects.nitrc.org/indi/retro/MPI_LEMON.html>`_ .
    """

    # Path Configuration

    this_dir = os.path.dirname(__file__)
    data_dir = os.path.join(this_dir,'..','_data')
    root_path = os.path.abspath(os.path.join(data_dir,'lemon'))
    os.makedirs(data_dir,exist_ok=True)

    # Download lemon Database

    urls = ['https://fcp-indi.s3.amazonaws.com/data/Projects/INDI/MPI-LEMON/Compressed_tar/EEG_MPILMBB_LEMON/EEG_Raw_BIDS_ID/sub-032301.tar.gz',
    'https://fcp-indi.s3.amazonaws.com/data/Projects/INDI/MPI-LEMON/Compressed_tar/EEG_MPILMBB_LEMON/EEG_Raw_BIDS_ID/sub-032302.tar.gz',
    'https://fcp-indi.s3.amazonaws.com/data/Projects/INDI/MPI-LEMON/Compressed_tar/EEG_MPILMBB_LEMON/EEG_Raw_BIDS_ID/sub-032303.tar.gz',
    'https://fcp-indi.s3.amazonaws.com/data/Projects/INDI/MPI-LEMON/name_match.csv']

    for url in urls:
        download(url,os.path.join(data_dir,'lemon'))

    # Generate all filepaths

    filepaths = _get_files(root_path)


    # Label Correction
    name_match = read_csv(os.path.join(root_path,'name_match.csv'))
    
    # Unpack files

    # TAR FILES
    tars = [x for x in filepaths if 'tar.gz' in x ]

    # SUBJECTS
    old_ids = [parse_from_regex(x,'(sub-.*?).tar.gz',['id']) for x in tars]
    old_ids = [x['id'] for x in old_ids]
    new_ids = [name_match.loc[(name_match.INDI_ID==x),'Initial_ID']._values[0] for x in old_ids]

    # EEG FILES
    not_tars = [x for x in filepaths if '.vhdr' in x ]
    not_tars_ids = [parse_from_regex(x,'RSEEG\\/(sub-.*?).vhdr',['id']) for x in not_tars]
    not_tars_ids = [x['id'] for x in not_tars_ids] 


    assert len(tars) == len(old_ids) == len(new_ids)

    if set(new_ids) == set(not_tars_ids): # all done
        return
    else:
        for file,old,new in zip(tars,old_ids,new_ids):
            if not new in not_tars_ids: # skip already prepared files
                shutil.unpack_archive(file,root_path)
                olddir = os.path.join(root_path,old)
                subject_files = _get_files(olddir)
                for subfile in subject_files:   # fix sub-id
                    new_path = subfile.replace(old,new)
                    dir,_ = os.path.split(new_path)
                    os.makedirs(dir,exist_ok=True)
                    shutil.move(subfile,new_path)
                shutil.rmtree(olddir)
    print('LEMON PREPARE DONE!')

def lemon_bidscoin_prepare(src_path):
    """Download and prepare a few files of the LEMON dataset to be used with BIDSCOIN.
    
    Parameters
    ----------
    src_path : str
        The path where the BIDSCOIN-ready LEMON files will be
    
    See Also
    --------
    
    datasets.lemon_prepare
    """
    lemon_prepare()
    this_dir = os.path.dirname(__file__)
    data_dir = os.path.join(this_dir,'..','_data')
    root_path = os.path.abspath(os.path.join(data_dir,'lemon'))
    bidscoin_input_path = src_path

    os.makedirs(bidscoin_input_path,exist_ok=True)

    files = _get_files(root_path)
    files = [x for x in files if x.split('.')[-1] in ['eeg','vmrk','vhdr'] ]

    files_out = []
    for f in files:
        session = 'ses-001'
        task = 'resting'
        head,tail=os.path.split(f)
        sub = tail.split('.')[0]
        new_path = os.path.join(bidscoin_input_path,sub,session,task,tail)
        files_out.append(new_path)

    for old,new in zip(files,files_out):
        print(old,' to ',new)
        os.makedirs(os.path.split(new)[0], exist_ok=True)
        if not os.path.isfile(new):
            shutil.copy2(old,new)
        else:
            print('already done, skipping...')
    print('finish')

def make_dummy_dataset(PATTERN='T%task%/S%session%/sub%subject%_%acquisition%_%run%',
    DATASET = 'DUMMY',
    NSUBS = 2,
    NSESSIONS = 2,
    NTASKS = 2,
    NACQS = 2,
    NRUNS = 2,
    NCHANNELS = 2,
    SFREQ = 200,
    STOP = 10,
    NUMEVENTS = 10,
    PREFIXES = {'subject':'SU','session':'SE','task':'TA','acquisition':'AC','run':'RU'},
    ROOT=None):
    """Create a dummy dataset given some parameters.
    
    Parameters
    ----------
    PATTERN : str, optional
        The pattern in placeholder notation using the following fields:
        %dataset%, %task%, %session%, %subject%, %run%, %acquisition%
    DATASET : str, optional
        Name of the dataset.
    NSUBS : int, optional
        Number of subjects.
    NSESSIONS : int, optional
        Number of sessions.
    NTASKS : int, optional
        Number of tasks.
    NACQS : int, optional
        Number of acquisitions.
    NRUNS : int, optional
        Number of runs.
    NCHANNELS : int, optional
        Number of channels.
    SFREQ : float, optional
        Samplinf frequency of the data.
    STOP : float, optional
        Time duration of the data in seconds.
    NUMEVENTS : int, optional
        Number of events along the duration.
    PREFIXES : dict, optional
        Dictionary with the following keys:'subject', 'session', 'task' and 'acquisition'.
        The values are the corresponding prefix. RUN is not present because it has to be a number.
    ROOT : str, optional
        Path where the files will be generated.
        If None, the _data subdir will be used.
    """

    if ROOT is None:
        this_dir = os.path.dirname(__file__)
        data_dir = os.path.abspath(os.path.join(this_dir,'..','_data'))
    else:
        data_dir = ROOT
    os.makedirs(data_dir,exist_ok=True)



    sub_zeros = get_num_digits(NSUBS)
    subs = [ PREFIXES['subject']+ str(x).zfill(sub_zeros) for x in range(NSUBS)]

    task_zeros = get_num_digits(NTASKS)
    tasks = [ PREFIXES['task']+str(x).zfill(task_zeros) for x in range(NTASKS)]

    run_zeros = get_num_digits(NRUNS)
    runs = [str(x).zfill(run_zeros) for x in range(NRUNS)]

    ses_zeros = get_num_digits(NSESSIONS)
    sessions = [ PREFIXES['session']+str(x).zfill(ses_zeros) for x in range(NSESSIONS)]

    acq_zeros = get_num_digits(NACQS)
    acquisitions = [ PREFIXES['acquisition']+str(x).zfill(acq_zeros) for x in range(NACQS)]

    # Create some dummy metadata
    n_channels = NCHANNELS
    sampling_freq = SFREQ  # in Hertz
    info = mne.create_info(n_channels, sfreq=sampling_freq)

    times = np.linspace(0, STOP, STOP*sampling_freq, endpoint=False)
    data = np.zeros((NCHANNELS,times.shape[0]))

    raw = mne.io.RawArray(data, info)
    raw.set_channel_types({x:'eeg' for x in raw.ch_names})
    new_events = mne.make_fixed_length_events(raw, duration=STOP//NUMEVENTS)

    for task in tasks:
        for session in sessions:
            for run in runs:
                for sub in subs:
                    for acq in acquisitions:
                        dummy = PATTERN.replace('%dataset%',DATASET)
                        dummy = dummy.replace('%task%',task)
                        dummy = dummy.replace('%session%',session)
                        dummy = dummy.replace('%subject%',sub)
                        dummy = dummy.replace('%run%',run)
                        dummy = dummy.replace('%acquisition%',acq)
                        path = [data_dir] +dummy.split('/')
                        fpath = os.path.join(*path)
                        _write_raw_brainvision(raw,fpath,new_events)

