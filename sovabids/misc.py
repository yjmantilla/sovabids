"Module with misc utils for sovabids."

import numpy as np

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


