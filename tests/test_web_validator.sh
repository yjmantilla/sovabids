#!/usr/bin/env bash
set -e
npm install --global npm@^7
npm install -g bids-validator
bids-validator _data/DUMMY/DUMMY_BIDS_placeholder_cli_vhdr/
# bids-validator _data/DUMMY_BIDS_placeholder_python_cnt/ 
# apparently it cannot download the cnt
bids-validator _data/DUMMY/DUMMY_BIDS_placeholder_python_vhdr/
bids-validator _data/DUMMY/DUMMY_BIDS_placeholder_rpc_vhdr/
bids-validator _data/DUMMY/DUMMY_BIDS_regex_cli_vhdr/
bids-validator _data/DUMMY/DUMMY_BIDS_regex_python_vhdr/
bids-validator _data/DUMMY/DUMMY_BIDS_regex_rpc_vhdr/


bids-validator _data/dummy_bidscoin_output
echo $?
# bids-validator _data/DUMMY/DUMMY_SOURCE