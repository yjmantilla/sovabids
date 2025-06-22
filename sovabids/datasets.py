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
import fileinput


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
    # ignore field so that it doesnt get rid of - or _
    old_ids = [parse_from_regex(x,'(sub-.*?).tar.gz',['ignore']) for x in tars]
    old_ids = [x['ignore'] for x in old_ids]
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

def make_dummy_dataset(EXAMPLE,
    PATTERN='T%task%/S%session%/sub%subject%_%acquisition%_%run%',
    DATASET = 'DUMMY',
    NSUBS = 2,
    NSESSIONS = 2,
    NTASKS = 2,
    NACQS = 2,
    NRUNS = 2,
    PREFIXES = {'subject':'SU','session':'SE','task':'TA','acquisition':'AC','run':'RU'},
    ROOT=None,
):
    """Create a dummy dataset given some parameters.
    
    Parameters
    ----------
    EXAMPLE : str,PathLike|list , required
        Path of the file to replicate as each file in the dummy dataset.
        If a list, it is assumed each item is a file. All of these items are replicated.
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
                        dirpath = os.path.join(*path[:-1])
                        os.makedirs(dirpath,exist_ok=True)
                        if isinstance(EXAMPLE,list):
                            for ff in EXAMPLE:
                                fname, ext = os.path.splitext(ff)
                                shutil.copyfile(ff, fpath+ext)
                                if 'vmrk' in ext or 'vhdr' in ext:
                                    replace_brainvision_filename(fpath+ext,path[-1])
                        else:
                            fname, ext = os.path.splitext(EXAMPLE)
                            shutil.copyfile(EXAMPLE, fpath+ext)


def generate_1_over_f_noise(n_channels, n_times, exponent=1.0, random_state=None):
    rng = np.random.default_rng(random_state)
    noise = np.zeros((n_channels, n_times))

    freqs = np.fft.rfftfreq(n_times, d=1.0)  # d=1.0 assumes unit sampling rate
    freqs[0] = freqs[1]  # avoid division by zero at DC

    scale = 1.0 / np.power(freqs, exponent)

    for ch in range(n_channels):
        # Generate white noise in time domain
        white = rng.standard_normal(n_times)
        # Transform to frequency domain
        white_fft = np.fft.rfft(white)
        # Apply 1/f scaling
        pink_fft = white_fft * scale
        # Transform back to time domain
        pink = np.fft.irfft(pink_fft, n=n_times)
        # Normalize to zero mean, unit variance
        pink = (pink - pink.mean()) / pink.std()
        noise[ch, :] = pink

    return noise

def get_dummy_raw(NCHANNELS = 5,
    SFREQ = 200,
    STOP = 10,
    NUMEVENTS = 10,
):
    """
    Create a dummy MNE Raw file given some parameters.

    Parameters
    ----------
    NCHANNELS : int, optional
        Number of channels.
    SFREQ : float, optional
        Sampling frequency of the data.
    STOP : float, optional
        Time duration of the data in seconds.
    NUMEVENTS : int, optional
        Number of events along the duration.
    """
    # Create some dummy metadata
    n_channels = NCHANNELS
    sampling_freq = SFREQ  # in Hertz
    info = mne.create_info(n_channels, sfreq=sampling_freq)

    times = np.linspace(0, STOP, STOP*sampling_freq, endpoint=False)
    data = generate_1_over_f_noise(NCHANNELS, times.shape[0], exponent=1.0)
    #np.zeros((NCHANNELS,times.shape[0]))

    raw = mne.io.RawArray(data, info)
    raw.set_channel_types({x:'eeg' for x in raw.ch_names})
    new_events = mne.make_fixed_length_events(raw, duration=STOP//NUMEVENTS)

    return raw,new_events

def save_dummy_vhdr(fpath,dummy_args={}
):
    """
    Save a dummy vhdr file.

    Parameters
    ----------
    fpath : str, required
        Path where to save the file.
    kwargs : dict, optional
        Dictionary with the arguments of the get_dummy_raw function.

    Returns
    -------
    List with the Paths of the desired vhdr file, if those were succesfully created,
    None otherwise.
    """

    raw,new_events = get_dummy_raw(**dummy_args)
    _write_raw_brainvision(raw,fpath,new_events,overwrite=True)
    eegpath =fpath.replace('.vhdr','.eeg')
    vmrkpath = fpath.replace('.vhdr','.vmrk')
    if all(os.path.isfile(x) for x in [fpath,eegpath,vmrkpath]):
        return [fpath,eegpath,vmrkpath]
    else:
        return None

def save_dummy_cnt(fpath,
):
    """
    Save a dummy cnt file.

    Parameters
    ----------
    fpath : str, required
        Path where to save the file.

    Returns
    -------
    Path of the desired file if the file was succesfully created,
    None otherwise.
    """
    fname = 'scan41_short.cnt'
    cnt_dict={'dataset_name': 'cnt_sample',
    'archive_name': 'scan41_short.cnt',
    'hash': 'md5:7ab589254e83e001e52bee31eae859db',
    'url': 'https://github.com/mne-tools/mne-testing-data/blob/master/CNT/scan41_short.cnt?raw=true',
    'folder_name': 'cnt_sample',
    }
    data_path = mne.datasets.fetch_dataset(cnt_dict)
    shutil.copyfile(os.path.join(data_path,'scan41_short.cnt'), fpath) #copyfile overwrites by default
    if os.path.isfile(fpath):
        return fpath
    else:
        return None

def replace_brainvision_filename(fpath,newname):
    if '.eeg' in newname:
        newname = newname.replace('.eeg','')
    if '.vmrk' in newname:
        newname = newname.replace('.vmrk','')
    for line in fileinput.input(fpath, inplace=True):
        if 'DataFile' in line:
            print(f'DataFile={newname}.eeg'.format(fileinput.filelineno(), line))
        elif 'MarkerFile' in line:
            print(f'MarkerFile={newname}.vmrk'.format(fileinput.filelineno(), line))
        else:
            print('{}'.format(line), end='')
