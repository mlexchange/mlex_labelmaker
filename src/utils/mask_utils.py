import os

from src.utils.data_utils import TiledDataLoader

mask_tiled_uri = os.getenv("MASK_TILED_URI")
mask_tiled_api_key = os.getenv("MASK_TILED_API_KEY", None)

tiled_mask = TiledDataLoader(mask_tiled_uri, mask_tiled_api_key)


def get_mask_options():
    """
    This function gets the mask options
    Returns:
        mask_options:       List of mask options
    """
    masks = tiled_mask.get_available_data_names()

    mask_options = [{"label": "None", "value": None}]

    for mask in masks:
        mask_options.append({"label": mask, "value": f"{mask_tiled_uri}/{mask}"})

    return mask_options
