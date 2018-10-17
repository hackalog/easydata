

def available_algorithms(keys_only=True):
    """Valid Algorithms for training or prediction

    This function simply returns a dict of known
    algorithms strings and their corresponding estimator function.

    Parameters
    ----------
    keys_only: boolean
        If True, return only keys. Otherwise, return a dictionary mapping keys to algorithms

    Valid Algorithms
    ----------------
    The valid algorithm names, and the function they map to, are:


    """
    _ALGORITHMS = {
    }
    if keys_only:
        return list(_ALGORITHMS.keys())
    return _ALGORITHMS
