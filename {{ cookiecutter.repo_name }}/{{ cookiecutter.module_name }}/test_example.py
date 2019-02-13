import unittest

def addition(n1, n2):
    """
    I'm a failing doctest. Please fix me.
    >>> addition(10, 12)
    20
    """
    return n1 - n2

def subtraction(n1, n2):
    """
    I'm subtraction.
    """
    return n1 + n2

class TestExercises(unittest.TestCase):
    def test_addition(self):
        """
        I'm a failing unittest. Fix me.
        """
        assert subtraction(5, 5) == 0

