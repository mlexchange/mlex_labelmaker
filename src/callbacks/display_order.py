import math
import os

import dash
import h5py
import numpy as np
from dash import ALL, Input, Output, State, callback
from dash.exceptions import PreventUpdate

from src.query import Query
from src.utils.data_utils import decompress_dict


@callback(
    Output("image-order", "data", allow_duplicate=True),
    Input({"base_id": "file-manager", "name": "total-num-data-points"}, "data"),
    Input("current-page", "value"),
    Input("similarity-on-off-indicator", "color"),
    Input("button-hide", "n_clicks"),
    Input("button-sort", "n_clicks"),
    Input("output-image-upload", "children"),
    State("probability-collapse", "is_open"),
    State("tab-group", "value"),
    State("previous-tab", "data"),
    State("thumbnail-num-cols", "value"),
    State("thumbnail-num-rows", "value"),
    State("similarity-model-list", "value"),
    State({"type": "thumbnail-image", "index": ALL}, "n_clicks_timestamp"),
    State({"type": "thumbnail-image", "index": ALL}, "n_clicks"),
    State("labels-dict", "data"),
    State("image-order", "data"),
    prevent_initial_call=True,
)
def update_image_order(
    num_imgs,
    current_page,
    similarity_on_off_color,
    button_hide_n_clicks,
    button_sort_n_clicks,
    new_content,
    probability_is_open,
    tab_selection,
    previous_tab,
    thumbnail_num_cols,
    thumbnail_num_rows,
    similarity_model,
    timestamp,
    thumb_n_clicks,
    labels_dict,
    current_image_order,
):
    """
    This callback arranges the image order according to the following actions:
        - New content is uploaded
        - Buttons sort or hidden are selected
        - Find similar images display has been activated or deactivated
    Args:
        num_imgs:                   Number of images in the dataset
        current_page:               Current page number
        similarity_on_off_color:    Color of the similarity-based search button
        button_hide_n_clicks:       Hide button
        button_sort_n_clicks:       Sort button
        new_content:                Display dimensions have changed
        probability_is_open:        Probability tab is open
        tab_selection:              Current tab [Manual, Similarity, Probability]
        previous_tab:               Previous tab
        thumbnail_num_cols:         Number of columns in the thumbnail display
        thumbnail_num_rows:         Number of rows in the thumbnail display
        similarity_model:           Selected similarity-based model
        timestamp:                  Timestamps of selected images in current page - to find similar
                                    images. Currently, one 1 image is selected for this operation
        thumb_n_clicks:             Number of clicks per card/filename in current page
        labels_dict:                Dictionary with labeling information, e.g.
                                    {filename1: [label1,label2], ...}
        current_image_order:        Current order of the images
    Returns:
        image_order:                Order of the images according to the selected action
                                    (sort, hide, new data, etc)
    """
    # Calculate the start and end index of the images to be displayed
    start_indx = thumbnail_num_cols * thumbnail_num_rows * current_page
    max_indx = min(start_indx + thumbnail_num_cols * thumbnail_num_rows, num_imgs)

    # Check if image order has been previously stored and load accordingly
    if os.path.exists(".current_image_order.hdf5"):
        if (
            button_sort_n_clicks
            and button_hide_n_clicks
            and button_hide_n_clicks % 2 == 1
            and button_sort_n_clicks % 2 == 1
        ):

            with h5py.File(".current_image_order.hdf5", "r") as f:
                ordered_indx = f["indices"]
                current_dataset_order = ordered_indx[:]

            os.remove(".current_image_order.hdf5")

            labels_dict = decompress_dict(labels_dict)
            query = Query(num_imgs=num_imgs, **labels_dict)
            ordered_indx = query.sort_labeled(current_dataset_order)

            with h5py.File(".current_image_order.hdf5", "w") as f:
                ordered_indx = np.array(ordered_indx)
                f.create_dataset("indices", data=ordered_indx)

            indices = list(range(start_indx, min(max_indx, ordered_indx.shape[0])))
            return ordered_indx[indices]
        else:
            with h5py.File(".current_image_order.hdf5", "r+") as f:
                ordered_indx = f["indices"]
                indices = list(range(start_indx, min(max_indx, ordered_indx.shape[0])))
                return ordered_indx[indices]

    # Check if the similarity-based search is activated
    elif similarity_on_off_color == "green":
        labels_dict = decompress_dict(labels_dict)
        query = Query(num_imgs=num_imgs, **labels_dict)

        # Check if the user has selected an image to find similar images
        for indx, n_click in enumerate(thumb_n_clicks):
            if n_click % 2 == 0 or timestamp[indx] is None:
                timestamp[indx] = 0
        clicked_ind = timestamp.index(max(timestamp))

        # If an image and model are selected, find similar images
        if clicked_ind is not None and similarity_model:
            ordered_indx = query.similarity_search(
                similarity_model,
                current_image_order[int(clicked_ind)],
            )

            with h5py.File(".current_image_order.hdf5", "w") as f:
                store_ordered_indx = np.array(ordered_indx)
                f.create_dataset("indices", data=store_ordered_indx)
        else:
            raise PreventUpdate

    # Check if the sort button is selected
    elif (
        button_sort_n_clicks
        and button_sort_n_clicks % 2 == 1
        and button_hide_n_clicks % 2 == 0
    ):
        labels_dict = decompress_dict(labels_dict)
        query = Query(num_imgs=num_imgs, **labels_dict)
        ordered_indx = query.sort_labeled()
        with h5py.File(".current_image_order.hdf5", "w") as f:
            store_ordered_indx = np.array(ordered_indx)
            f.create_dataset("indices", data=store_ordered_indx)
        ordered_indx = np.array(ordered_indx)

    # Check if the hide button is selected
    elif button_hide_n_clicks and button_hide_n_clicks % 2 == 1:
        labels_dict = decompress_dict(labels_dict)
        query = Query(num_imgs=num_imgs, **labels_dict)
        ordered_indx = query.hide_labeled()
        with h5py.File(".current_image_order.hdf5", "w") as f:
            store_ordered_indx = np.array(ordered_indx)
            f.create_dataset("indices", data=store_ordered_indx)
        ordered_indx = np.array(ordered_indx)

    # Otherwise, return page indices
    else:
        return list(range(start_indx, max_indx))

    indices = list(range(start_indx, min(max_indx, len(ordered_indx))))
    image_order = ordered_indx[indices]

    return image_order


@callback(
    Output("image-order", "data"),
    Input("button-hide", "n_clicks"),
    Input("button-sort", "n_clicks"),
)
def undo_sort_or_hide_labeled_images(
    button_hide_n_clicks,
    button_sort_n_clicks,
):
    if (
        button_sort_n_clicks
        and button_hide_n_clicks
        and button_hide_n_clicks % 2 == 1
        and button_sort_n_clicks % 2 == 1
    ):
        raise PreventUpdate
    if os.path.exists(".current_image_order.hdf5"):
        os.remove(".current_image_order.hdf5")
    return dash.no_update


@callback(
    Output("current-page", "value", allow_duplicate=True),
    Input({"base_id": "file-manager", "name": "total-num-data-points"}, "data"),
    Input("first-page", "n_clicks"),
    Input("find-similar-unsupervised", "n_clicks"),
    Input("button-sort", "n_clicks"),
    prevent_initial_call=True,
)
def go_to_first_page(
    num_imgs,
    button_first_page,
    button_find_similar_images,
    button_sort_n_clicks,
):
    """
    Update the current page to the first page
    """
    return 0


@callback(
    Output("current-page", "value", allow_duplicate=True),
    Input("prev-page", "n_clicks"),
    State("current-page", "value"),
    prevent_initial_call=True,
)
def go_to_prev_page(
    button_prev_page,
    current_page,
):
    """
    Update the current page to the previous page
    """
    current_page = current_page - 1
    return current_page


@callback(
    Output("current-page", "value", allow_duplicate=True),
    Input("next-page", "n_clicks"),
    State("current-page", "value"),
    prevent_initial_call=True,
)
def go_to_next_page(
    button_next_page,
    current_page,
):
    """
    Update the current page to the next page
    """
    current_page = current_page + 1
    return current_page


@callback(
    Output("current-page", "value", allow_duplicate=True),
    Input("last-page", "n_clicks"),
    State({"base_id": "file-manager", "name": "total-num-data-points"}, "data"),
    State("thumbnail-num-rows", "value"),
    State("thumbnail-num-cols", "value"),
    State("button-hide", "n_clicks"),
    prevent_initial_call=True,
)
def go_to_last_page(
    button_last_page,
    num_imgs,
    thumbnail_num_rows,
    thumbnail_num_cols,
    button_hide_n_clicks,
):
    """
    Update the current page to the last page
    """
    if button_hide_n_clicks and button_hide_n_clicks % 2 == 1:
        if os.path.exists(".current_image_order.hdf5"):
            with h5py.File(".current_image_order.hdf5", "r") as f:
                ordered_indx = f["indices"]
                num_imgs = len(ordered_indx)
    current_page = math.ceil(num_imgs / (thumbnail_num_rows * thumbnail_num_cols)) - 1
    return current_page


@callback(
    Output("current-page", "value", allow_duplicate=True),
    Input("current-page", "value"),
    State({"base_id": "file-manager", "name": "total-num-data-points"}, "data"),
    State("thumbnail-num-rows", "value"),
    State("thumbnail-num-cols", "value"),
    prevent_initial_call=True,
)
def go_to_users_input(
    current_page,
    num_imgs,
    thumbnail_num_rows,
    thumbnail_num_cols,
):
    """
    Update the current page to user's direct input
    """
    max_num_pages = math.ceil((num_imgs // thumbnail_num_cols) / thumbnail_num_rows)
    if current_page > max_num_pages:
        current_page = max_num_pages - 1
        return current_page
    else:
        raise PreventUpdate


@callback(
    [
        [Output("first-page", "disabled"), Output("prev-page", "disabled")],
        [Output("next-page", "disabled"), Output("last-page", "disabled")],
        Input("current-page", "value"),
        State({"base_id": "file-manager", "name": "total-num-data-points"}, "data"),
        State("thumbnail-num-cols", "value"),
        State("thumbnail-num-rows", "value"),
        State("button-hide", "n_clicks"),
    ],
    prevent_initial_call=True,
)
def disable_buttons(
    current_page,
    num_imgs,
    thumbnail_num_cols,
    thumbnail_num_rows,
    button_hide_n_clicks,
):
    """
    Disable first and last page buttons based on the current page
    """
    if button_hide_n_clicks and button_hide_n_clicks % 2 == 1:
        if os.path.exists(".current_image_order.hdf5"):
            with h5py.File(".current_image_order.hdf5", "r") as f:
                ordered_indx = f["indices"]
                num_imgs = len(ordered_indx)
    max_num_pages = math.ceil((num_imgs // thumbnail_num_cols) / thumbnail_num_rows)
    return (
        2 * [current_page == 0],
        2 * [max_num_pages <= current_page + 1],
    )
