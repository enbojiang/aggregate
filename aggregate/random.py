# hold global random state

import numpy as np

__all__ = ['RANDOM', 'set_seed']


# global default RNG for all random numbers
RANDOM = np.random.default_rng(None)

def set_seed(seed):
    """
    Fix the seed for the global random number generator. Ensures reproducibility.

    """
    global RANDOM
    RANDOM = np.random.default_rng(seed)
