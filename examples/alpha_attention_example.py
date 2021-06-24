import sys,os

from osfclient.models import file
from sovabids.utils import create_dir
from osfclient.cli import fetch,_setup_osf
from osfclient.utils import norm_remote_path, split_storage, makedirs, checksum
this_dir = os.path.dirname(__file__)
data_dir = os.path.abspath(os.path.join(this_dir,'..','_data'))
create_dir(data_dir)

root = os.path.join('Raw_data','EEG_raw_data')

def fetch2(args):
    """Fetch an individual file from a project.

    The first part of the remote path is interpreted as the name of the
    storage provider. If there is no match the default (osfstorage) is
    used.

    The local path defaults to the name of the remote file.

    If the project is private you need to specify a username.

    If args.force is True, write local file even if that file already exists.
    If args.force is False but args.update is True, overwrite an existing local
    file only if local and remote files differ.
    """
    osf = _setup_osf(args)
    project = osf.project(args.project)
    storage, remote_path = split_storage(args.remote)

    store = project.storage(storage)

    if isinstance(args.locals,list) and isinstance(args.remotes,list):
         check = [os.path.exists(x) and not args.force and not args.update for x in args.locals]
         if all(check):
             print('All files exist already, not overwriting')
             return 
         print('building filelist, this may take a while')
         filelist = list(store.files)
         print('filelist ready')

         for (local,remote) in zip(args.locals,args.remotes):
            local_path = local
            _, remote_path = split_storage(remote)

            if local_path is None:
                _, local_path = os.path.split(remote_path)

            local_path_exists = os.path.exists(local_path)
            if local_path_exists and not args.force and not args.update:
                sys.exit("Local file %s already exists, not overwriting." % local_path)

            directory, _ = os.path.split(local_path)
            if directory:
                makedirs(directory, exist_ok=True)

            osf = _setup_osf(args)
            project = osf.project(args.project)

            #store = project.storage(storage)
            for file_ in filelist:
                if norm_remote_path(file_.path) == remote_path:
                    if local_path_exists and not args.force and args.update:
                        if file_.hashes.get('md5') == checksum(local_path):
                            print("Local file %s already matches remote." % local_path)
                    with open(local_path, 'wb') as fp:
                        file_.write_to(fp)

    else:
        local_path = args.local
        if local_path is None:
            _, local_path = os.path.split(remote_path)

        local_path_exists = os.path.exists(local_path)
        if local_path_exists and not args.force and not args.update:
            sys.exit("Local file %s already exists, not overwriting." % local_path)

        directory, _ = os.path.split(local_path)
        if directory:
            makedirs(directory, exist_ok=True)

        osf = _setup_osf(args)
        project = osf.project(args.project)

        store = project.storage(storage)
        for file_ in store.files:
            if norm_remote_path(file_.path) == remote_path:
                if local_path_exists and not args.force and args.update:
                    if file_.hashes.get('md5') == checksum(local_path):
                        print("Local file %s already matches remote." % local_path)
                        break
                with open(local_path, 'wb') as fp:
                    file_.write_to(fp)

                # only fetching one file so we are done
                break


subs = [[26,27],[24,25]]
tasks = ['Experiment1_rawdata','Experiment2_rawdata']
extensions = ['vhdr','eeg','vmrk']
pattern = 'sub%subject%_%run%.%extension%'
runs = [1,2]

files = []
filepaths = []
targetpaths = []

for task,sub_list in zip(tasks,subs):
    for sub in sub_list:
        for run in runs:
            for ext in extensions:
                filename = pattern.replace('%subject%', "{:02d}".format(sub))
                filename = filename.replace('%run%',str(run))
                filename = filename.replace('%extension%',ext)
                files.append(filename)
                path = os.path.join(root,task)
                targetpath = os.path.join(data_dir,path)
                create_dir(targetpath)
                filepaths.append(os.path.join(path,filename).replace('\\','/'))
                targetpaths.append(os.path.join(targetpath,filename).replace('\\','/'))

print(targetpaths)
projectid = 'pa4yg'
 
# for source,target in zip(filepaths,targetpaths):
#     args = {'remote':source,'local':target,'project':projectid,'force':False,'update':True,'username':None}
#     args = type('Args', (object,), args)
#     fetch2(args)
    #os.system('osf -p {} fetch {} {}'.format(projectid,source,target))
args = {'remotes':filepaths,'locals':targetpaths,'remote':filepaths[0],'local':targetpaths[0],'project':projectid,'force':False,'update':False,'username':None}
args = type('Args', (object,), args)
fetch2(args)
