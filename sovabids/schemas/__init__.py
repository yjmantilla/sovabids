import os
this_dir = os.path.dirname(__file__)

def get_sova2coin_bidsmap():
    """Get the sova2coin bidsmap.

    Returns:
    --------

    str :
        The sova2coin bidsmap.

    """
    bidsmap_sova2coin_file = os.path.join(this_dir,'bidsmap_sova2coin.yml')
    with open(bidsmap_sova2coin_file) as f:
        bidsmap_sova2coin = f.read()
    return bidsmap_sova2coin

