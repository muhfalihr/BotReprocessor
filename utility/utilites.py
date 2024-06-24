import hashlib

from typing import *
from datetime import datetime

def hashing(string: str, algorithm='md5') -> str:
    """
    Hashes multiline text into a single line using the specified algorithm.

    Args:
        text (str): The multiline text to be hashed.
        algorithm (str): The hashing algorithm to use. Default is 'md5'.
                         Supported algorithms are 'md5', 'sha1', 'sha256', and 'sha512'.

    Returns:
        str: The hashed text in hexadecimal format.

    Raises:
        ValueError: If the specified algorithm is not supported.
    """
    # Dictionary of supported algorithms
    algorithms = {
        'md5': hashlib.md5,
        'sha1': hashlib.sha1,
        'sha256': hashlib.sha256,
        'sha512': hashlib.sha512
    }

    # Check if the algorithm is supported
    if algorithm not in algorithms:
        raise ValueError(f"Unsupported algorithm '{algorithm}'. Supported algorithms are: {', '.join(algorithms.keys())}")
    
    combined_text = ''.join(string.splitlines())
    hash_object = algorithms[algorithm](combined_text.encode())
    hash_hex = hash_object.hexdigest()
    
    return hash_hex

def view_log(log_path: str, num_bytes=1000):
    """
    Reads the last num_bytes from a given file.

    Args:
        file_path (str): The path to the file to be read.
        num_bytes (int): The number of bytes to read from the end of the file. Default is 10000 bytes.

    Returns:
        bytes: The last num_bytes from the file.
    """
    with open(f"{log_path}/debug.log", "rb") as file:
        file.seek(0, 2)
        file_size = file.tell()
        
        if file_size > num_bytes:
            file.seek(-num_bytes, 2)
        else:
            file.seek(0)
        return file.read()