import os
this_dir = os.path.dirname(__file__)

bidsmap_sova2coin_file = os.path.join(this_dir,'bidsmap_sova2coin.yml')
with open(bidsmap_sova2coin_file) as f:
    bidsmap_sova2coin = f.read()

