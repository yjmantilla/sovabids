"Module with misc utilities for sovabids."

import sys
import numpy as np

# Unicode characters that look like hyphens but break CLI argument parsing.
# Users often get these by copy-pasting from word processors or PDFs.
_UNICODE_DASHES = {
    '‐': '-',  # HYPHEN
    '‑': '-',  # NON-BREAKING HYPHEN
    '‒': '-',  # FIGURE DASH
    '–': '-',  # EN DASH
    '—': '-',  # EM DASH
    '―': '-',  # HORIZONTAL BAR
    '−': '-',  # MINUS SIGN
}

def handle_unicode_dashes():
    """Replace Unicode dash characters in sys.argv with regular hyphens.

    Word processors and some terminals substitute hyphens with typographic
    dashes (em dash, en dash, etc.). This causes cryptic argparse errors.
    Call this before parse_args() in every CLI entry point.
    """
    found = []
    for i, arg in enumerate(sys.argv[1:], 1):
        new_arg = arg
        for dash, hyphen in _UNICODE_DASHES.items():
            if dash in new_arg:
                found.append((i, arg, dash))
                new_arg = new_arg.replace(dash, hyphen)
        sys.argv[i] = new_arg
    if found:
        print(
            "WARNING: Unicode dash character(s) detected in command-line arguments "
            "and replaced with standard hyphens. This often happens when copying "
            "commands from a word processor or PDF. The following arguments were affected:"
        )
        for idx, original, dash in found:
            print(f"  argv[{idx}]: {original!r}  (contained U+{ord(dash):04X} {dash})")

def flat_paren_counter(string):
    """Count the number of non-nested balanced parentheses in the string. If parenthesis is not balanced then return -1.

    Parameters
    ----------

    string : str
        The string we will inspect for balanced parentheses.
    
    Returns
    -------

    int :
        The number of non-nested balanced parentheses or -1 if the string has unbalanced parentheses.
    """
    #Modified from
    #jeremy radcliff
    #https://codereview.stackexchange.com/questions/153078/balanced-parentheses-checker-in-python
    counter = 0
    times = 0
    inside = False
    for c in string:
        if not inside and c == '(':
            counter += 1
            inside = True
        elif inside and c == ')':
            counter -= 1
            times +=1
            inside = False
        if counter < 0:
            return -1

    if counter == 0:
        return times
    return -1



def get_num_digits(N):
    """Return the number of digits of the given number N.
    
    Parameters
    ----------
    N : int
        The number we want to apply the function to.
    
    Returns
    -------
    int :
        The numbers of digits needed to represent the number N.
    """
    return int(np.log10(N))+1


