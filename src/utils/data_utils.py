import base64
import gzip
import hashlib
import json
import logging

import httpx
from humanhash import humanize
from tiled.client import from_uri

logger = logging.getLogger(__name__)


class TiledDataLoader:
    def __init__(self, data_tiled_uri, data_tiled_api_key):
        self.data_tiled_uri = data_tiled_uri
        self.data_tiled_api_key = data_tiled_api_key
        self.refresh_data_client()

    def refresh_data_client(self):
        try:
            self.data_client = from_uri(
                self.data_tiled_uri,
                api_key=self.data_tiled_api_key,
                timeout=httpx.Timeout(30.0),
            )
        except Exception as e:
            logger.warning(f"Error connecting to Tiled: {e}")
            self.data_client = None

    def check_dataloader_ready(self):
        """
        Check if the data client is available and ready to be used.
        If base_only is True, only check the base uri.
        """
        if self.data_client is None:
            # Try refreshing once
            self.refresh_data_client()
            return False if self.data_client is None else True
        else:
            try:
                headers = {"Authorization": f"Bearer {self.data_tiled_api_key}"}
                httpx.get(self.data_tiled_uri, headers=headers)
            except Exception as e:
                logger.warning(f"Error connecting to Tiled: {e}")
                return False
        return True

    def prepare_project_container(self, user, project_name):
        """
        Prepare a project container in the data store
        """
        last_container = self.data_client
        for part in [user, project_name, "labels"]:
            if part in last_container.keys():
                last_container = last_container[part]
            else:
                last_container = last_container.create_container(key=part)
        return last_container

    def get_data_by_trimmed_uri(self, trimmed_uri, slice=None):
        """
        Retrieve data by a trimmed uri (not containing the base uri) and slice id
        """
        if slice is None:
            return self.data_client[trimmed_uri]
        else:
            return self.data_client[trimmed_uri][slice]

    def get_metadata_by_trimmed_uri(self, trimmed_uri):
        """
        Retrieve metadata by a trimmed uri (not containing the base uri)
        """
        return self.data_client[trimmed_uri].metadata


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
