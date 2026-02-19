from bidscoin.plugins.sova2coin import is_sourcefile
from pathlib import Path
from bidscoin.bidscoiner import bidscoiner
from bidscoin.bidsmapper import bidsmapper
import os
import shutil
from sovabids.schemas import get_sova2coin_bidsmap
from sovabids.files import _get_files
from sovabids.settings import REPO_PATH
from sovabids.parsers import _modify_entities_of_placeholder_pattern
from sovabids.datasets import lemon_bidscoin_prepare,make_dummy_dataset,save_dummy_vhdr
import yaml

def test_sova2coin(dataset='dummy_bidscoin',noedit=True):
    data_dir = os.path.join(REPO_PATH,'_data')
    data_dir = os.path.abspath(data_dir)
    os.makedirs(data_dir,exist_ok=True)

    source_path = os.path.abspath(os.path.join(data_dir,dataset+'_input'))
    bids_path= os.path.abspath(os.path.join(data_dir,dataset+'_output'))
    rules_path = os.path.join(data_dir,'bidscoin_'+dataset+'_rules.yml')
    template_path = os.path.join(data_dir,'bidscoin_template.yml')

    if dataset == 'dummy_bidscoin':
      pat = 'sub-%entities.subject%/ses-%entities.session%/eeg-%entities.task%-%entities.run%.vhdr'
      rules = {
        'entities': None,
        'dataset_description':{'Name':dataset},
        'non-bids':{
          'path_analysis':
          {'pattern':pat}
        }
      }
    elif dataset=='lemon_bidscoin':
      rules ={
      'entities':{'task':'resting'},
      'dataset_description':{'Name':dataset},
      'sidecar':{'PowerLineFrequency':50,'EEGReference':'FCz'},
      'channels':{'type':{'VEOG':'VEOG'}},
      'non-bids':{'path_analysis':{'pattern':'sub-%entities.subject%/ses-%entities.session%/%ignore%/%ignore%.vhdr'}}
      }

    with open(rules_path, 'w') as outfile:
      yaml.dump(rules, outfile, default_flow_style=False)


    #CLEAN BIDS PATH
    for dir in [bids_path,source_path]:
      try:
          shutil.rmtree(dir)
      except:
          pass

    if dataset=='lemon_bidscoin':
      lemon_bidscoin_prepare(source_path)
    else:
      pat = _modify_entities_of_placeholder_pattern(rules['non-bids']['path_analysis']['pattern'],'cut')
      pat = pat.replace('.vhdr','')
      try:
        shutil.rmtree(source_path)
      except:
        pass
      
      # Make example VHDR File
      example_fpath = save_dummy_vhdr(os.path.join(data_dir,'dummy.vhdr'))

      make_dummy_dataset(EXAMPLE=example_fpath,DATASET=dataset+'_input',NSUBS=3,NTASKS=2,NSESSIONS=2,NACQS=1,NRUNS=2,PATTERN=pat,ROOT=source_path)


    files = _get_files(source_path)
    any_vhdr = Path([x for x in files if '.vhdr' in x][0])
    any_not_vhdr = Path([x for x in files if '.vhdr' not in x][0])

    assert is_sourcefile(any_vhdr)=='EEG'
    assert is_sourcefile(any_not_vhdr)==''
    # if dataset=='lemon_bidscoin':
    #   assert get_attribute('EEG',any_vhdr,'sidecar.SamplingFrequency') == 2500.0
    # else:
    #   assert get_attribute('EEG',any_vhdr,'sidecar.SamplingFrequency') == 200.0

    bidsmap = get_sova2coin_bidsmap().format(rules_path)

    with open(template_path,mode='w') as f:
        f.write(bidsmap)

    bidsmapper(rawfolder=source_path,bidsfolder=bids_path,subprefix='sub-',sesprefix='ses-',bidsmapfile='bidsmap.yaml',templatefile= template_path,noedit=noedit)

    bidscoiner(rawfolder    = source_path,
                bidsfolder   = bids_path)

if __name__ == '__main__':
    noedit=False
    test_sova2coin(noedit=noedit)
    #test_sova2coin('lemon_bidscoin',noedit=noedit)