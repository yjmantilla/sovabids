#!/usr/bin/env bash
set -e
npm install --global npm@^7
npm install -g bids-validator
bids-validator _data/DUMMY/DUMMY_BIDS_custom_python
bids-validator _data/DUMMY/DUMMY_BIDS_regex_python
bids-validator _data/DUMMY/DUMMY_BIDS_custom_cli
bids-validator _data/DUMMY/DUMMY_BIDS_regex_cli
bids-validator _data/DUMMY/DUMMY_BIDS_custom_rpc
bids-validator _data/DUMMY/DUMMY_BIDS_regex_rpc
bids-validator _data/DUMMY/DUMMY_BIDS_custom_cli
bids-validator _data/DUMMY/DUMMY_BIDS_regex_cli

bids-validator _data/dummy_bidscoin_output
echo $?
#bids-validator _data/DUMMY/DUMMY_SOURCE