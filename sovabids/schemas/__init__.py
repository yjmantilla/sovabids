"""Module with the schemas associated with sovabids."""
import os

def get_sova2coin_bidsmap():
    """Get the sova2coin bidsmap.

    Returns
    -------

    str :
        The sova2coin bidsmap.

    """
    this_dir = os.path.dirname(__file__)
    bidsmap_sova2coin_file = os.path.join(this_dir,'bidsmap_sova2coin.yml')
    with open(bidsmap_sova2coin_file) as f:
        bidsmap_sova2coin = f.read()
    return bidsmap_sova2coin

