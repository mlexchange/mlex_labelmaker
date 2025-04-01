import base64
import gzip
import hashlib
import json

from humanhash import humanize


def compress_dict(data):
    """
    This function compresses a dictionary and returns a base64 encoded string.
    Args:
        data:   Dictionary to be compressed
    Returns:
        base64_data:    Base64 encoded string
    """
    json_data = json.dumps(data).encode("utf-8")
    compressed_data = gzip.compress(json_data)
    base64_data = base64.b64encode(compressed_data).decode("utf-8")
    return base64_data


def decompress_dict(base64_data):
    """
    This function decompresses a base64 encoded string and returns the original data.
    Args:
        base64_data:    Base64 encoded string
    Returns:
        data:           Original data
    """
    compressed_data = base64.b64decode(base64_data)
    json_data = gzip.decompress(compressed_data)
    data = json.loads(json_data.decode("utf-8"))
    return data


def hash_list_of_strings(strings_list):
    """
    Produces a hash of a list of strings.
    """
    concatenated = "".join(strings_list)
    digest = hashlib.sha256(concatenated.encode("utf-8")).hexdigest()
    return humanize(digest)
