import logging
import time

import dash
import numpy as np
import pandas as pd
from dash import ALL, Input, Output, State, callback
from dash.exceptions import PreventUpdate

from src.labels import Labels
from src.utils.data_utils import compress_dict, decompress_dict
from src.utils.plot_utils import create_label_component

logger = logging.getLogger(__name__)


@callback(
    Output("color-picker-modal", "is_open"),
    Input({"type": "color-label-button", "index": ALL}, "n_clicks"),
    Input("modify-label-button", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_color_picker_modal(color_label_n_clicks, submit_n_clicks):
    """
    This callback toggles the color picker modal for label color definition
    Args:
        color_label_n_clicks:       Number of clicks in all the label color buttons
        submit_n_clicks:            Number of clicks in submit color button
    Returns:
        Opens or closes the color picker modal
    """
    if any(color_label_n_clicks):
        return True
    elif submit_n_clicks:
        return False
    else:
        return dash.no_update


@callback(
    Output({"type": "label-percentage", "index": ALL}, "value"),
    Output({"type": "label-percentage", "index": ALL}, "label"),
    Output("total_labeled", "children"),
    Input("labels-dict", "data"),
    State({"base_id": "file-manager", "name": "total-num-data-points"}, "data"),
    State({"type": "label-percentage", "index": ALL}, "value"),
)
def update_labeling_progress(labels_dict, num_imgs, current_label_perc_value):
    """
    This callback updates the label percentage values
    Args:
        labels_dict:                    Dictionary of labeled images, e.g.,
                                        {filename1: [label1, label2], ...}
        num_imgs:                       Total number of images in the dataset
        current_label_perc_value:       Current label percentage values
    Returns:
        label_perc_value:               Numerical values that indicate the percentage of images
                                        labeled per class/label
        label_perc_label:               Same as above, but string
        total_labeled:                  Message to indicate how many images have been labeled
    """
    labels_dict = decompress_dict(labels_dict)
    labels = Labels(**labels_dict)
    label_perc_value, label_perc_label, total_labeled = labels.get_labeling_progress(
        num_imgs
    )
    if len(label_perc_value) != len(current_label_perc_value):
        raise PreventUpdate
    return label_perc_value, label_perc_label, total_labeled


@callback(
    Output("labels-dict", "data", allow_duplicate=True),
    Input("keybind-event-listener", "event"),
    State({"type": "thumbnail-image", "index": ALL}, "n_clicks"),
    State("labels-dict", "data"),
    State({"type": "label-button", "index": ALL}, "children"),
    State("image-order", "data"),
    prevent_initial_call=True,
)
def label_selected_thumbnails_key_binds(
    keybind_label,
    thumbnail_image_select_value,
    labels_dict,
    label_button_children,
    image_order,
):
    """
    This callback updates the dictionary of labeled images when a new image is labeled with key binds
    Args:
        keybind_label:                  Keyword entry
        thumbnail_image_select_value:   Selected thumbnail image (n_clicks)
        labels_dict:                    Dictionary of labeled images, e.g.,
                                        {filename1: [label1, label2], ...}
        label_button_children:          List of label text in label buttons
        image_order:                    Order of the images
    Returns:
        labels_dict:                    Dictionary with labeling information, e.g.
                                        {filename1: [label1, label2], ...}
    """
    start = time.time()
    labels_dict = decompress_dict(labels_dict)
    labels = Labels(**labels_dict)
    if "key" in keybind_label:
        if (
            keybind_label["key"].isdigit()
            and keybind_label["ctrlKey"] is True
            and int(keybind_label["key"]) - 1 in range(len(label_button_children))
        ):
            label_class_value = label_button_children[int(keybind_label["key"]) - 1]
            labels.manual_labeling(
                label_class_value, thumbnail_image_select_value, image_order
            )
        else:
            raise PreventUpdate
    logger.debug(f"Updating labels after {time.time()-start}")
    return compress_dict(labels.to_dict())


@callback(
    Output("labels-dict", "data", allow_duplicate=True),
    Input({"base_id": "file-manager", "name": "data-project-dict"}, "data"),
    State("labels-dict", "data"),
    State({"type": "label-button", "index": ALL}, "children"),
    prevent_initial_call=True,
)
def label_selected_thumbnails_new_dataset(
    data_project_dict,
    labels_dict,
    label_button_children,
):
    """
    This callback updates the dictionary of labeled images when a new dataset is loaded
    Args:
        data_project_dict:              Data project information
        labels_dict:                    Dictionary of labeled images, e.g.,
                                        {filename1: [label1, label2], ...}
        label_button_children:          List of label text in label buttons
    Returns:
        labels_dict:                    Dictionary with labeling information, e.g.
                                        {filename1: [label1, label2], ...}
    """
    start = time.time()
    labels_dict = decompress_dict(labels_dict)
    labels = Labels(**labels_dict)
    labels.init_labels(label_button_children)
    logger.debug(f"Updating labels after {time.time()-start}")
    return compress_dict(labels.to_dict())


@callback(
    Output("labels-dict", "data", allow_duplicate=True),
    Input("probability-label", "n_clicks"),
    State("probability-model-list", "value"),
    State("labels-dict", "data"),
    State("probability-threshold", "value"),
    State("probability-label-name", "value"),
    prevent_initial_call=True,
)
def label_selected_thumbnails_probability(
    probability_label_button,
    probability_model,
    labels_dict,
    threshold,
    probability_label,
):
    """
    Args:
        probability_label_button:       Triggers labeling with probability results
        probability_model:              Selected probability-based model
        labels_dict:                    Dictionary of labeled images, e.g.,
                                        {filename1: [label1, label2], ...}
        threshold:                      Threshold value for labeling with probability
        probability_label:              Selected label to be assigned with probability model
    Returns:
        labels_dict:                    Dictionary with labeling information, e.g.
                                        {filename1: [label1, label2], ...}
    """
    start = time.time()
    labels_dict = decompress_dict(labels_dict)
    labels = Labels(**labels_dict)
    if probability_model:
        labels.probability_labeling(probability_model, probability_label, threshold)
    else:
        raise PreventUpdate
    logger.debug(f"Updating labels after {time.time()-start}")
    return compress_dict(labels.to_dict())


@callback(
    Output("labels-dict", "data", allow_duplicate=True),
    Input("un-label", "n_clicks"),
    State({"type": "thumbnail-image", "index": ALL}, "n_clicks"),
    State("labels-dict", "data"),
    State("image-order", "data"),
    prevent_initial_call=True,
)
def unlabel_selected_thumbnails(
    unlabel_button,
    thumbnail_image_select_value,
    labels_dict,
    image_order,
):
    """
    Args:
        unlabel_button:                 Un-label button
        thumbnail_image_select_value:   Selected thumbnail image (n_clicks)
        labels_dict:                    Dictionary of labeled images, e.g.,
                                        {filename1: [label1, label2], ...}
        image_order:                    Order of the images
    Returns:
        labels_dict:                    Dictionary with labeling information, e.g.
                                        {filename1: [label1, label2], ...}
    """
    start = time.time()
    labels_dict = decompress_dict(labels_dict)
    labels = Labels(**labels_dict)
    labels.manual_labeling(None, thumbnail_image_select_value, image_order)
    logger.debug(f"Updating labels after {time.time()-start}")
    return compress_dict(labels.to_dict())


@callback(
    Output("labels-dict", "data", allow_duplicate=True),
    Input({"type": "label-button", "index": ALL}, "n_clicks_timestamp"),
    State({"type": "thumbnail-image", "index": ALL}, "n_clicks"),
    State("labels-dict", "data"),
    State({"type": "label-button", "index": ALL}, "children"),
    State("image-order", "data"),
    prevent_initial_call=True,
)
def label_selected_thumbnails(
    label_button_n_clicks,
    thumbnail_image_select_value,
    labels_dict,
    label_button_children,
    image_order,
):
    """
    This callback updates the dictionary of labeled images when a new image is labeled
    Args:
        label_button_n_clicks:          List of timestamps of the clicked label-buttons
        thumbnail_image_select_value:   Selected thumbnail image (n_clicks)
        labels_dict:                    Dictionary of labeled images, e.g.,
                                        {filename1: [label1, label2], ...}
        label_button_children:          List of label text in label buttons
        image_order:                    Order of the images
    Returns:
        labels_dict:                    Dictionary with labeling information, e.g.
                                        {filename1: [label1, label2], ...}
    """
    if all(click == 0 for click in label_button_n_clicks):
        raise PreventUpdate
    start = time.time()
    labels_dict = decompress_dict(labels_dict)
    labels = Labels(**labels_dict)
    indx = np.argmax(label_button_n_clicks)
    label_class_value = label_button_children[indx]
    labels.manual_labeling(label_class_value, thumbnail_image_select_value, image_order)
    logger.debug(f"Updating labels after {time.time()-start}")
    return compress_dict(labels.to_dict())


@callback(
    Output("label-buttons", "children", allow_duplicate=True),
    Output("labels-dict", "data", allow_duplicate=True),
    Output("color-cycle", "data"),
    Input("modify-label-button", "n_clicks"),
    State("labels-dict", "data"),
    State({"type": "color-label-button", "index": ALL}, "n_clicks_timestamp"),
    State("label-color-picker", "value"),
    State("color-cycle", "data"),
    State("modify-label-name", "value"),
    prevent_initial_call=True,
)
def modify_label(
    modify_label_n_clicks,
    labels_dict,
    color_label_t_clicks,
    new_color,
    color_cycle,
    new_label_name,
):
    """
    This callback modifies an existing label name and color
    Args:
        modify_label_n_clicks:          Number of clicks in modify label button
        labels_dict:                    Dictionary of labeled images, e.g.,
                                        {filename1: [label1, label2], ...}
        color_label_t_clicks:           List of timestamps of the clicked label-color buttons
        new_color:                      New color for the label
        color_cycle:                    List of label colors
        new_label_name:                 New label name
    Returns:
        label_comp:                     Updated label buttons
        labels_dict:                    Dictionary with labeling information, e.g.
                                        {filename1: [label1, label2], ...}
        color_cycle:                    List of label colors
    """
    start = time.time()
    labels_dict = decompress_dict(labels_dict)
    labels = Labels(**labels_dict)
    mod_indx = color_label_t_clicks.index(max(color_label_t_clicks))
    color_cycle[mod_indx] = new_color["hex"]
    if new_label_name != "":
        label_to_rename = labels.labels_list[mod_indx]
        labels.update_labels_list(rename_label=label_to_rename, new_name=new_label_name)
    label_comp = create_label_component(labels.labels_list, color_cycle)
    logger.debug(f"Updating labels after {time.time()-start}")
    return label_comp, compress_dict(labels.to_dict()), color_cycle


@callback(
    Output("label-buttons", "children", allow_duplicate=True),
    Output("labels-dict", "data", allow_duplicate=True),
    Output("color-cycle", "data", allow_duplicate=True),
    Input({"type": "delete-label-button", "index": ALL}, "n_clicks_timestamp"),
    State("labels-dict", "data"),
    State("color-cycle", "data"),
    prevent_initial_call=True,
)
def delete_label(
    del_label_n_clicks,
    labels_dict,
    color_cycle,
):
    if all(click == 0 for click in del_label_n_clicks):
        raise PreventUpdate
    start = time.time()
    labels_dict = decompress_dict(labels_dict)
    labels = Labels(**labels_dict)
    indx_label_to_delete = np.argmax(del_label_n_clicks)
    label_to_delete = labels.labels_list[indx_label_to_delete]
    labels.update_labels_list(remove_label=label_to_delete)
    color_cycle.pop(indx_label_to_delete)
    label_comp = create_label_component(labels.labels_list, color_cycle)
    logger.debug(f"Updating labels after {time.time()-start}")
    return label_comp, compress_dict(labels.to_dict()), color_cycle


@callback(
    Output("label-buttons", "children", allow_duplicate=True),
    Output("labels-dict", "data", allow_duplicate=True),
    Input("modify-list", "n_clicks"),
    State("add-label-name", "value"),
    State("labels-dict", "data"),
    State("color-cycle", "data"),
    prevent_initial_call=True,
)
def add_new_label(
    modify_list_n_clicks,
    add_label_name,
    labels_dict,
    color_cycle,
):
    start = time.time()
    labels_dict = decompress_dict(labels_dict)
    labels = Labels(**labels_dict)
    labels.update_labels_list(add_label=add_label_name)
    label_comp = create_label_component(labels.labels_list, color_cycle)
    logger.debug(f"Updating labels after {time.time()-start}")
    return label_comp, compress_dict(labels.to_dict())


@callback(
    Output("label-buttons", "children", allow_duplicate=True),
    Output("probability-label-name", "options", allow_duplicate=True),
    Output("labels-dict", "data", allow_duplicate=True),
    Input("probability-model-list", "value"),
    State("labels-dict", "data"),
    State("color-cycle", "data"),
    prevent_initial_call=True,
)
def load_labels_from_probabilities(
    probability_model,
    labels_dict,
    color_cycle,
):
    start = time.time()
    labels_dict = decompress_dict(labels_dict)
    labels = Labels(**labels_dict)
    if probability_model:
        df_prob = pd.read_parquet(probability_model)
        probability_labels = list(df_prob.columns[0:])
        additional_labels = list(set(probability_labels) - set(labels.labels_list))
        for additional_label in additional_labels:
            labels.update_labels_list(add_label=additional_label)
        probability_options = [
            {"label": name, "value": name} for name in probability_labels
        ]
    else:
        raise PreventUpdate
    label_comp = create_label_component(labels.labels_list, color_cycle)
    logger.debug(f"Updating labels after {time.time()-start}")
    return label_comp, probability_options, compress_dict(labels.to_dict())


@callback(
    Output("event-id", "options"),
    Output("modal-load-tiled", "is_open"),
    Input("button-load-tiled", "n_clicks"),
    Input("confirm-load-tiled", "n_clicks"),
    State("labels-dict", "data"),
    State("project-name", "data"),
    prevent_initial_call=True,
)
def load_from_tiled_modal(load_n_click, confirm_load, labels_dict, project_name):
    """
    Load labels from tiled associated with the project_name
    Args:
        load_n_click:       Number of clicks in load from tiled button
        confirm_load:       Number of clicks in confim button within loading from tiled modal
        labels_dict:        Dictionary of labeled images, e.g.,
                            {filename1: [label1, label2], ...}
        project_name:       Name of the current project
    Returns:
        event_id:           Available tagging event IDs associated with the current data project
        modal_load_tiled:   True/False to open/close loading from tiled modal
    """
    changed_id = dash.callback_context.triggered[-1]["prop_id"]
    if (
        changed_id == "confirm-load-tiled.n_clicks"
    ):  # if confirmed, load chosen tagging event
        return dash.no_update, False

    labels_dict = decompress_dict(labels_dict)
    labels = Labels(**labels_dict)
    options = labels.get_events_ids(project_name)
    return options, True
