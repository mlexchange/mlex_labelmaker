import itertools
import logging
import os
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from functools import partial
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

from src.utils.data_utils import TiledDataLoader

logging.basicConfig(encoding="utf-8", level=logging.INFO)


LABELS_TILED_URI = os.getenv("LABELS_TILED_URI", "http://localhost:8888")
LABELS_TILED_API_KEY = os.getenv("LABELS_TILED_API_KEY", None)
USER = os.getenv("USER", "user")

labels_tiled_dataloader = TiledDataLoader(LABELS_TILED_URI, LABELS_TILED_API_KEY)


class Labels:
    def __init__(self, labels_dict, labels_list, num_imgs_per_label=None) -> None:
        self.labels_dict = labels_dict
        self.labels_list = labels_list
        if num_imgs_per_label is None:
            self.num_imgs_per_label = self.get_num_imgs_per_label()
        else:
            self.num_imgs_per_label = num_imgs_per_label
        pass

    def to_dict(self):
        return {
            "labels_dict": self.labels_dict,
            "labels_list": self.labels_list,
            "num_imgs_per_label": self.num_imgs_per_label,
        }

    def init_labels(self, labels_list=None):
        """
        Initializes the labels dictionary
        Args:
            filenames:      List of filenames within the data set
            labels_list:    List of current available labels
        """
        if labels_list:
            self.labels_list = labels_list
        self.labels_dict = {}
        self.num_imgs_per_label = self.get_num_imgs_per_label()
        pass

    def get_num_imgs_per_label(self):
        """
        Calculates the labeling progress in terms of number of labeled images
        Returns:
            num_imgs_per_label:     Number of labeled images per label
        """
        assigned_labels = list(itertools.chain.from_iterable(self.labels_dict.values()))
        num_imgs_per_label = {}
        for label_index in range(len(self.labels_list)):
            num_imgs_per_label[str(label_index)] = assigned_labels.count(label_index)
        return num_imgs_per_label

    def update_labels_list(
        self, add_label=None, remove_label=None, rename_label=None, new_name=None
    ):
        """
        Updates the labels list
        Args:
            add_label:          New label to be added to the list
            remove_label:       Label to be removed from the list and dictionary (if this label has
                                been used to label at least 1 image within the data set)
        """
        if add_label is not None:
            self.labels_list.append(add_label)
            self.num_imgs_per_label[str(len(self.labels_list) - 1)] = 0
        elif remove_label is not None:
            remove_index = self.labels_list.index(remove_label)
            self.labels_list.remove(remove_label)

            new_labels_dict = {}
            for key, values in self.labels_dict.items():
                new_values_list = []
                for val in values:
                    if val != remove_index:
                        if val > remove_index:
                            new_values_list.append(val - 1)
                        else:
                            new_values_list.append(val)
                new_labels_dict[str(key)] = new_values_list
            self.labels_dict = new_labels_dict

            self.num_imgs_per_label.pop(str(remove_index))
            num_imgs_per_label = self.num_imgs_per_label.items()
            for key, value in list(num_imgs_per_label):
                if int(key) > remove_index:
                    self.num_imgs_per_label[str(int(key) - 1)] = value
                    self.num_imgs_per_label.pop(key)

        elif rename_label is not None and new_name is not None:
            mod_indx = self.labels_list.index(rename_label)
            self.labels_list[mod_indx] = new_name
        pass

    def _get_labeled_indices(self):
        return [int(k) for k, v in self.labels_dict.items() if v != []]

    def assign_labels(self, label, indices_to_label, overwrite=True):
        """
        Assign labels in dictionary with or without overwriting existing labels
        Args:
            label:                  Label to be assigned
            indices_to_label:       List of indexes to be labeled
            overwrite:              If True, the new label will overwrite any existing label in the
                                    dictionary, ow the label is not overwritten and the new label is
                                    ignored when the image is already labeled
        """
        if not overwrite:
            labeled_indices = self._get_labeled_indices()
            indices_to_label = list((set(indices_to_label) - set(labeled_indices)))
        for index in indices_to_label:
            current_labels = self.labels_dict.get(str(index), [])
            if current_labels:
                self.num_imgs_per_label[str(current_labels[0])] -= 1
            if label is None:
                self.labels_dict[index] = []
            else:
                label_index = self.labels_list.index(label)
                self.labels_dict[index] = [label_index]
                self.num_imgs_per_label[str(label_index)] += 1
        pass

    def probability_labeling(self, probability_model, probability_label, threshold):
        """
        Labeling process through probability-based trained model. This process will not overwrite
        existing labels in the dictionary
        Args:
            probability_model:      Probability-based model outcome to be used for labeling
            probability_label:      Label to be assigned across the data set
            threshold:              Probability threshold to assign labels
        """
        df_prob = pd.read_parquet(probability_model)
        indices = np.where(df_prob[probability_label] > threshold / 100)[0].tolist()
        self.assign_labels(probability_label, indices, overwrite=False)
        pass

    def manual_labeling(self, label, num_clicks, img_indexes):
        """
        Manual labeling process where highlighted images (odd number of clicks) are labeled
        Args:
            label:          Label to be assigned
            num_clicks:     List of number of clicks per image
            img_indexes:    List of indexes corresponding to the images in the data set
        """
        indexes_to_label = []
        for clicks, img_index in zip(num_clicks, img_indexes):
            if clicks is not None:
                if clicks % 2 == 1:
                    indexes_to_label.append(img_index)
        self.assign_labels(label, indexes_to_label)
        pass

    def load_tiled_labels(self, data_project, event_id, project_name, set_progress):
        """
        Query labels from tiled
        Args:
            project_name:     Data project_name
            event_id:      [str] Event id
            project_name:     Data project_name
            set_progress:   [dbc.Progress] Progress bar
        """
        # Get the labels from the tagging event in tiled
        expected_url = f"/{USER}/{project_name}/labels/{event_id}"
        event_client = labels_tiled_dataloader.get_data_by_trimmed_uri(expected_url)
        labels = list(event_client)
        len_dataset = len(labels)

        self.init_labels()  # resets dict and label before loading data
        for indx, label in enumerate(labels):
            label_metadata = event_client[label].metadata
            uri = label_metadata["uri"]
            label = label_metadata["label"]
            if label not in self.labels_list:
                self.update_labels_list(add_label=label)
            index = data_project.get_index(uri)
            self.assign_labels(label, [index])
            set_progress(indx / len_dataset * 100)
        pass

    def get_events_ids(self, project_name):
        trimmed_uri = f"/{USER}/{project_name}/labels"
        labels_client = labels_tiled_dataloader.get_data_by_trimmed_uri(trimmed_uri)
        event_options = []
        for event_id in labels_client.keys():
            expected_url = f"/{USER}/{project_name}/labels/{event_id}"
            event_metadata = labels_tiled_dataloader.get_metadata_by_trimmed_uri(
                expected_url
            )
            tagger_id = event_metadata.get("tagger_id", "Unknown")
            tagging_event_time = event_metadata.get("run_time", "Unknown")
            event_options.append(
                {
                    "label": f"Tagger ID: {tagger_id}, modified: {tagging_event_time}",
                    "value": event_id,
                }
            )
        return event_options

    def save_to_tiled(self, tagger_id, data_project, project_name, set_progress):
        """
        Save labels to tiled
        Args:
            tagger_id:      [str] Tagger id
            datasets:       [list of dict] Data Project
            project_name:     Data project_name
            set_progress:   [dbc.Progress] Progress bar
        """
        event_id = str(uuid4())
        labels_client = labels_tiled_dataloader.prepare_project_container(
            USER, project_name
        )
        event_client = labels_client.create_container(
            key=event_id,
            metadata={"tagger_id": tagger_id, "run_time": str(datetime.utcnow())},
        )

        # Define partial function to save one dataset to tiled
        partial_save_label_to_tiled = partial(
            self._save_label_to_tiled,
            labels_list=self.labels_list,
            project_name=project_name,
            event_id=event_id,
            tiled_client=event_client,
        )

        indexes = self.labels_dict.keys()
        indexes = list(map(int, indexes))
        uri_list = data_project.read_datasets(indexes, just_uri=True)

        # Save all datasets to tiled
        with ThreadPoolExecutor() as executor:
            # Start all the tasks
            futures = {
                executor.submit(partial_save_label_to_tiled, uri, labels)
                for uri, labels in zip(uri_list, self.labels_dict.values())
            }

            for i, future in enumerate(as_completed(futures), 1):
                future.result()
                set_progress(i / len(futures) * 100)
        return event_client.uri

    @staticmethod
    def _save_label_to_tiled(
        uri,
        label_index,
        labels_list,
        project_name,
        event_id,
        tiled_client,
    ):
        if len(label_index) > 0:
            label = labels_list[label_index[0]]
            # TODO: Add support for multiple labels per image

            label_id = str(uuid4())
            label_metadata = {
                "uri": uri,
                "type": "tiled" if "http" in uri else "file",
                "label": str(label),
            }

            try:
                tiled_client.create_container(key=label_id, metadata=label_metadata)
            except Exception as e:
                logging.error(f"Error: {e}")
                return f"Data set: {uri} with label {label} ended with status {e}."
        pass

    def save_to_table(self, data_project, set_progress):
        """
        Save labels to a table
        Args:
            data_project:   Data project
            set_progress:   [dbc.Progress] Progress bar
        Returns:
            Table with labels
        """
        labels_table = pd.DataFrame(columns=["uri", "label"])
        num_labeled = len(self.labels_dict)
        for index, labels in self.labels_dict.items():
            if len(labels) > 0:
                label = self.labels_list[labels[0]]
                uri = data_project.read_datasets([int(index)], just_uri=True)[0]
                new_row = pd.DataFrame({"uri": [uri], "label": [label]})
                labels_table = pd.concat([labels_table, new_row], ignore_index=True)
            set_progress(len(labels_table) / num_labeled * 100)

        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file_name = temp_file.name
        temp_file.close()

        # Save the DataFrame to the temporary file as CSV
        labels_table.to_csv(temp_file_name, index=False)

        return temp_file_name

    def save_to_directory(self, data_project, set_progress):
        """
        Zips images with labels to be downloaded
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            data_path = os.path.join(temp_dir, "downloaded_images")

            # Get the system's temporary directory
            tmp_dir = tempfile.gettempdir()

            # create a folder per label
            for label_key in self.labels_list:
                label_index = self.labels_list.index(label_key)
                if self.num_imgs_per_label[str(label_index)] > 0:
                    label_dir = data_path / Path(label_key)
                    label_dir.mkdir(parents=True, exist_ok=True)

            # save images to the corresponding label folder
            indexes = self.labels_dict.keys()
            imgs, uris = data_project.read_datasets(
                list(map(int, indexes)),
                export="pillow",
                resize=False,
            )

            with ThreadPoolExecutor() as executor:
                futures = []
                for index, (_, label_index) in enumerate(self.labels_dict.items()):
                    if len(label_index) > 0:
                        save_image = partial(
                            self._save_image,
                            data_path,
                            self.labels_list[label_index[0]],
                            imgs[index],
                            uris[index],
                        )
                        # Submit the function to the executor
                        futures.append(executor.submit(save_image))

                # Print the progress
                for i, future in enumerate(as_completed(futures), 1):
                    set_progress(i / len(futures) * 100)

            archive_path = os.path.join(tmp_dir, "results")
            shutil.make_archive(archive_path, "zip", data_path)
        return archive_path

    @staticmethod
    def _save_image(data_path, label, image, uri):
        label_dir = f"{data_path}/{label}"
        base_name = uri.split("/")[-1].split(".")[0]
        filename = Path(f"{base_name}.tif")
        i = 0  # check duplicate uri and save under different name if needed
        while filename.exists():
            filename = Path(f"{label_dir}/{base_name}_{i}.tif")
            i += 1
        image.save(f"{label_dir}/{filename}")
        pass

    def get_labeling_progress(self, total_num_images):
        """
        Calculates the labeling progress
        Args:
            total_num_images:   Total number of images in the data set
        Returns:
            progress_values:    [float] Percentage of images assigned to each label
            progress_labels:    [str] Number of images assigned to each label
            totral_num_labeled: [str] Message displaying how many images have been labeled and how
                                many images are in the data set
        """
        num_imgs_per_label = list(self.num_imgs_per_label.values())
        progress_values = list(
            100 * np.array(num_imgs_per_label) / max(np.sum(num_imgs_per_label), 1)
        )
        progress_labels = list(map(str, num_imgs_per_label))
        total_num_labeled = (
            f"Labeled {int(np.sum(num_imgs_per_label))} out of {total_num_images}"
        )
        return progress_values, progress_labels, total_num_labeled
