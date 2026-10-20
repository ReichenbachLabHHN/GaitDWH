"""
This module contains helper functions to load the fact data from HuGaDB database into a harmonized database.
NOTE: This file was originally provided by the HuGaDB and was altered and extended.
"""

"""Function for downloading data from HuGaDB file."""
import numpy as np

def extract_data(path_to_file):
    """Read HuGaDB data from file and get numpy matrix
        Parameters:
            path_to_file: string
                path to HuGaDB file.
        Return: 2d-array 
            Data in numpy format 
    """
    return np.genfromtxt(path_to_file, delimiter='\t', skip_header=4)




def extract_header(path_to_file):
    """
    Extracts the header (first three lines) of the provided file.

    Args:
        path_to_file (string):
            The filepath leading to the file in question

    Returns:
        (string):
            The extracted header
    """
    with open(path_to_file) as f:
        header = f.readlines()[3]
    return header


def extract_date(path_to_file):
    """
    Extracts the data from the provided file.

    Args:
        path_to_file (string):
            The filepath leading to the file in question

    Returns:
        (string):
            The extracted date
    """
    with open(path_to_file) as f:
        data = f.readlines()[2]
    return data[6:]

def extract_person_ID(path_to_file):
    """
    Extracts the local person_ID from the provided file.

    Args:
        path_to_file (string):
            The filepath leading to the file in question

    Returns:
        (string):
            The extracted person_ID
    """
    return path_to_file[-9:-7]