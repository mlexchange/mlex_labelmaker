import logging
import os
from itertools import chain

import numpy as np
from scipy.spatial.distance import cdist

from src.labels import Labels
from src.utils.data_utils import TiledDataLoader

logging.basicConfig(encoding="utf-8", level=logging.INFO)

RESULTS_TILED_URI = os.getenv("RESULTS_TILED_URI", "")
RESULTS_TILED_API_KEY = os.getenv("RESULTS_TILED_API_KEY", None)

results_tiled_dataloader = TiledDataLoader(RESULTS_TILED_URI, RESULTS_TILED_API_KEY)


class Query(Labels):
    def __init__(self, num_imgs, **kwargs):
        super().__init__(**kwargs)
        self.num_imgs = num_imgs
        pass

    def sort_labeled(self, dataset_order=None):
        labeled = {}
        for key, label in self.labels_dict.items():
            if len(label) > 0:
                labeled.setdefault(label[0], []).append(int(key))
        labeled_indices = list(chain(*labeled.values()))
        if dataset_order is not None:
            dataset_order = set(dataset_order)
            labeled_indices = set(labeled_indices) & dataset_order
            unlabeled_indices = list(dataset_order - labeled_indices)
            labeled_indices = list(labeled_indices)
        else:
            unlabeled_indices = list(set(range(self.num_imgs)) - set(labeled_indices))
        return labeled_indices + unlabeled_indices

    def hide_labeled(self):
        labeled_indices = self._get_labeled_indices()
        unlabeled_indices = set(range(self.num_imgs)) - set(labeled_indices)
        return list(unlabeled_indices)

    def similarity_search(self, trimmed_uri, index_interest):
        unlabeled_indx = self.hide_labeled()  # Get list of indexes of unlabeled images
        df_model = results_tiled_dataloader.get_data_by_trimmed_uri(trimmed_uri).read()
        dist = cdist(
            df_model.iloc[index_interest, :].values[np.newaxis, :],
            df_model.loc[unlabeled_indx].values,
            "cosine",
        ).squeeze()
        ordered_indx = np.array(unlabeled_indx)[np.argsort(dist)]
        return ordered_indx
