import os
import time

import dash
from dash import ALL, MATCH, Input, Output, State, callback, ctx
from dash.exceptions import PreventUpdate
from file_manager.data_project import DataProject

from src.app_layout import TILED_KEY, cache, logger
from src.labels import labels_tiled_dataloader
from src.query import Query
from src.utils.data_utils import decompress_dict, hash_list_of_strings
from src.utils.plot_utils import draw_rows, parse_full_screen_content


@callback(
    Output("project-name", "data"),
    Input({"base_id": "file-manager", "name": "data-project-dict"}, "data"),
    prevent_initial_call=True,
)
def update_project_name(data_project_dict):
    data_project = DataProject.from_dict(data_project_dict)
    data_uris = [dataset.uri for dataset in data_project.datasets]
    project_name = hash_list_of_strings(data_uris)
    return project_name


@callback(
    Output({"type": "thumbnail-card", "index": ALL}, "style"),
    Output({"type": "thumbnail-name", "index": ALL}, "children"),
    Output({"type": "thumbnail-src", "index": ALL}, "src"),
    Output({"type": "thumbnail-image", "index": ALL}, "n_clicks"),
    Input("image-order", "data"),
    Input({"base_id": "file-manager", "name": "data-project-dict"}, "data"),
    Input("log-transform", "value"),
    Input("min-max-percentile", "value"),
    State("labels-dict", "data"),
    State("similarity-on-off-indicator", "color"),
    State("thumbnail-num-cols", "value"),
    State("thumbnail-num-rows", "value"),
    prevent_initial_call=True,
)
@cache.memoize(timeout=0)
def update_output(
    image_order,
    data_project_dict,
    log,
    percentiles,
    labels_dict,
    similarity_on_off_color,
    thumbnail_num_cols,
    thumbnail_num_rows,
):
    """
    This callback displays images in the front-end
    Args:
        image_order:            Order of the images according to the selected action (sort, hide,
                                new data, etc)
        current_page:           Index of the current page
        log:                    Log toggle
        percentiles:            Min-Max Percentile
        labels_dict:            Dictionary with labeling information, e.g.
                                {filename1: [label1,label2], ...}
        data_project_dict:      Data project information
        find_similar_images:    Find similar images button, n_clicks
        tab_selection:          Current tab [Manual, Similarity, Probability]
        card_id:                Card ID to identify the card index
        thumbnail_num_cols:     Number of thumbnail columns
        thumbnail_num_rows:     Number of thumbnail rows
    Returns:
        style:                  Image card style
        filename:               Filename label in image card
        content:                Content to be displayed in image card
        init_clicks:            Initial number of clicks in image card
    """
    if percentiles is None:
        percentiles = [0, 100]
    num_imgs_per_page = thumbnail_num_cols * thumbnail_num_rows
    none_style = {"display": "none"}
    labels_dict = decompress_dict(labels_dict)

    if data_project_dict == {}:
        return (
            [none_style] * num_imgs_per_page,
            [dash.no_update] * num_imgs_per_page,
            [dash.no_update] * num_imgs_per_page,
            [dash.no_update] * num_imgs_per_page,
        )

    data_project = DataProject.from_dict(data_project_dict, api_key=TILED_KEY)
    if len(data_project.datasets) == 0:
        return (
            [none_style] * num_imgs_per_page,
            [dash.no_update] * num_imgs_per_page,
            [dash.no_update] * num_imgs_per_page,
            [dash.no_update] * num_imgs_per_page,
        )

    start = time.time()
    # Load labels and data project
    contents, uris = data_project.read_datasets(
        image_order, resize=True, log=log, percentiles=percentiles
    )
    logger.debug(f"Data project done after {time.time()-start}")

    uris = uris + [""] * (num_imgs_per_page - len(contents))
    contents = contents + [""] * (num_imgs_per_page - len(contents))
    styles = [{"margin-bottom": "0px", "margin-top": "10px"}] * len(image_order) + [
        none_style
    ] * (num_imgs_per_page - len(image_order))

    # Find similar images has been activated
    if similarity_on_off_color == "green":
        init_clicks = 1
        query = Query(
            num_imgs=data_project.datasets[-1].cumulative_data_count, **labels_dict
        )
        unlabeled_indices = query.hide_labeled()
        init_clicks = [1 if image in unlabeled_indices else 0 for image in image_order]
    else:
        init_clicks = [0] * len(uris)

    init_clicks += [0] * (num_imgs_per_page - len(init_clicks))
    logger.debug(f"Display done after {time.time()-start}")
    return (
        styles,
        uris,
        contents,
        init_clicks,
    )


@callback(
    Output("label-dict-per-page", "data"),
    Input("image-order", "data"),
    Input("labels-dict", "data"),
    prevent_initial_call=True,
)
def update_label_dict_per_page(image_order, labels_dict):
    labels_dict = decompress_dict(labels_dict)
    labels_dict_per_page = {
        "labels_dict": {
            str(key): labels_dict["labels_dict"][str(key)]
            for key in image_order
            if str(key) in labels_dict["labels_dict"]
        },
        "labels_list": labels_dict["labels_list"],
    }
    return labels_dict_per_page


@callback(
    Output({"type": "thumbnail-prob", "index": ALL}, "children"),
    Output({"type": "thumbnail-prob", "index": ALL}, "style"),
    Input("image-order", "data"),
    Input("probability-model-list", "value"),
    Input("tab-group", "value"),
    State("probability-collapse", "is_open"),
    State("thumbnail-num-cols", "value"),
    State("thumbnail-num-rows", "value"),
    prevent_initial_call=True,
)
def update_probabilities(
    image_order,
    probability_model,
    tab_selection,
    probability_is_open,
    thumbnail_num_cols,
    thumbnail_num_rows,
):
    num_imgs_per_page = thumbnail_num_cols * thumbnail_num_rows
    if probability_model and tab_selection == "probability":
        df_prob = labels_tiled_dataloader.get_data_by_trimmed_uri(
            probability_model
        ).read()
        probs = df_prob.iloc[image_order]
        probs = [
            " \n".join([f"{col}: {row[col]*100:.2f}" for col in probs.columns])
            for _, row in probs.iterrows()
        ]
        if len(probs) < num_imgs_per_page:
            probs += [""] * (num_imgs_per_page - len(probs))
        prob_style = [
            {
                "display": "block",
                "whiteSpace": "pre-wrap",
                "font-size": "12px",
                "margin-bottom": "0px",
                "margin-top": "1px",
            }
        ] * len(probs)
        return (
            probs,
            prob_style,
        )
    return [dash.no_update] * num_imgs_per_page, [
        {"display": "none"}
    ] * num_imgs_per_page


@callback(
    Output("output-image-upload", "children"),
    Input("thumbnail-num-cols", "value"),
    Input("thumbnail-num-rows", "value"),
)
def update_rows(thumbnail_num_cols, thumbnail_num_rows):
    """
    This callback prepares the image cards according to the number of rows selected by the user
    Args:
        thumbnail-num-cols:     Number of columns selected by the user
        thumbnail-num-rows:     Number of rows selected by the user

    Returns:
        children:               Images to be displayed in front-end according to the current page
                                index and # of columns
    """
    children = draw_rows(thumbnail_num_rows, thumbnail_num_cols)
    return children


@callback(
    Output({"type": "full-screen-modal", "index": ALL}, "children"),
    Output({"type": "full-screen-modal", "index": ALL}, "is_open"),
    Output({"type": "double-click-entry", "index": ALL}, "n_events"),
    Input({"type": "double-click-entry", "index": ALL}, "n_events"),
    State({"base_id": "file-manager", "name": "data-project-dict"}, "data"),
    State("log-transform", "value"),
    State("min-max-percentile", "value"),
    State("image-order", "data"),
    prevent_initial_call=True,
)
def full_screen_thumbnail(
    double_click, data_project_dict, log, percentiles, image_order
):
    """
    This callback opens the modal pop-up window with the full size image that was double-clicked
    Args:
        double_click:               List of number of times that every card has been double-clicked
        data_project_dict:          Data project information
        log:                        Log toggle
        percentiles:                Min-Max Percentile
        image_order:                Order of the images according to the selected action (sort,hide)
    Returns:
        contents:                   Contents for pop-up window
        open_modal:                 Open/close modal
        double_click:               Resets the number of double-clicks to zero
    """
    if 1 not in double_click:
        raise PreventUpdate
    if percentiles is None:
        percentiles = [0, 100]
    data_project = DataProject.from_dict(data_project_dict, api_key=TILED_KEY)
    img_contents, img_uri = data_project.read_datasets(
        [image_order[double_click.index(1)]],
        resize=False,
        log=log,
        percentiles=percentiles,
    )
    contents = parse_full_screen_content(img_contents, img_uri)
    return [contents], [True], [0] * len(double_click)


@callback(
    Output({"type": "thumbnail-card", "index": MATCH}, "color", allow_duplicate=True),
    Input({"type": "thumbnail-image", "index": MATCH}, "n_clicks"),
    Input("label-dict-per-page", "data"),
    State("color-cycle", "data"),
    State({"type": "thumbnail-card", "index": MATCH}, "color"),
    State({"type": "thumbnail-card", "index": MATCH}, "id"),
    State("image-order", "data"),
    prevent_initial_call=True,
)
def select_thumbnail(
    value, labels_dict, color_cycle, current_color, card_id, image_order
):
    """
    This callback assigns a color to thumbnail cards in the following scenarios:
        - An image has been selected, but no label has been assigned (blue)
        - An image has been labeled (label color)
        - An image has been unselected or unlabeled (no color)
    Args:
        value:                      Thumbnail card that triggered the callback (n_clicks)
        labels_dict:                Dictionary of labeled images, as follows: {'img1':[], 'img2':[]}
        color_cycle:                List that contains the color cycle associated with the labels
        current_color:              Current color in thumbnail card
        card_id:                    Card ID to identify the card index
        image_order:                Order of the images according to the selected action (sort,hide)
    Returns:
        thumbnail_color:            Color of thumbnail card
    """
    if value is None:
        color = current_color
    elif value % 2 == 1:
        color = "primary"
    else:
        card_index = card_id["index"]
        color = "white"
        if card_index < len(image_order):
            if str(image_order[card_index]) in labels_dict["labels_dict"].keys():
                label = labels_dict["labels_dict"][str(image_order[card_index])]
                if len(label) > 0:
                    label_indx = label[0]
                    color = color_cycle[label_indx]
    if color == current_color:
        return dash.no_update
    return color


@callback(
    Output({"type": "thumbnail-card", "index": MATCH}, "color", allow_duplicate=True),
    Output(
        {"type": "thumbnail-image", "index": MATCH}, "n_clicks", allow_duplicate=True
    ),
    Input("keybind-event-listener", "event"),
    prevent_initial_call=True,
)
def select_all_keybind(keybind_label):
    """
    This callback selects all the thumbnail cards using the keybind
    Args:
        keybind_label:          Keyword entry
    Returns:
        Modify the color of the thumbnail card
    """
    keybind_is_valid = True
    if "key" in keybind_label:
        keybind_is_valid = keybind_label["key"] == "a" and keybind_label["ctrlKey"]
        if not keybind_is_valid:
            raise PreventUpdate
    return "primary", 1


@callback(
    Output({"type": "thumbnail-image", "index": ALL}, "n_clicks", allow_duplicate=True),
    Input({"type": "label-button", "index": ALL}, "n_clicks_timestamp"),
    Input("un-label", "n_clicks"),
    Input("confirm-un-label-all", "n_clicks"),
    Input("keybind-event-listener", "event"),
    State({"type": "thumbnail-image", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def deselect(
    label_button_trigger, unlabel_n_clicks, unlabel_all, keybind_label, thumb_clicked
):
    """
    This callback deselects a thumbnail card
    Args:
        label_button_trigger:   Label button
        unlabel_n_clicks:       Un-label button
        unlabel_all:            Un-label all the images
        keybind_label:          Keyword entry
        thumb_clicked:          Selected thumbnail card indice, e.g., [0,1,1,0,0,0]
    Returns:
        Modify the number of clicks for a specific thumbnail card
    """
    changed_id = ctx.triggered_id
    keybind_is_valid = True
    if changed_id == "keybind-event-listener" and "key" in keybind_label:
        keybind_is_valid = (
            keybind_label["key"].isdigit()
            and keybind_label["ctrlKey"]
            and int(keybind_label["key"]) - 1 in range(len(label_button_trigger))
        )
        if not keybind_is_valid:
            raise PreventUpdate
    if (
        all(x is None for x in label_button_trigger)
        and unlabel_n_clicks is None
        and unlabel_all is None
        and not keybind_is_valid
    ):
        return [dash.no_update] * len(thumb_clicked)
    return [0 for thumb in thumb_clicked]


@callback(
    Output("button-hide", "children"),
    Input("button-hide", "n_clicks"),
    State("button-hide", "children"),
    prevent_initial_call=True,
)
def update_hide_button_text(n_clicks, current_text):
    if current_text == "Hide" and n_clicks != 0:
        return "Unhide"
    return "Hide"


@callback(
    Output("button-sort", "children"),
    Input("button-sort", "n_clicks"),
    State("button-sort", "children"),
    prevent_initial_call=True,
)
def update_sort_button_text(n_clicks, current_text):
    if current_text == "Sort" and n_clicks != 0:
        return "Undo Sort"
    return "Sort"


@callback(
    Output("similarity-on-off-indicator", "color", allow_duplicate=True),
    Output("similarity-on-off-indicator", "label", allow_duplicate=True),
    Input("find-similar-unsupervised", "n_clicks"),
    State("similarity-model-list", "value"),
    prevent_initial_call=True,
)
def display_indicator_on(n_clicks, similarity_model):
    """
    This callback controls the light indicator in the DataClinic tab, which indicates whether the
    similarity-based image display is ON or OFF
    Args:
        n_clicks:           The button "Find Similar Images" triggers this callback
        similarity_model:   Selected similarity-based model
    Returns:
        color:              Indicator color
        label:              Indicator label
    """
    if similarity_model is None:
        raise PreventUpdate
    file_path = ".current_image_order.hdf5"
    if os.path.exists(file_path):
        os.remove(file_path)
    return "green", "Find Similar Images: ON"


@callback(
    Output("similarity-on-off-indicator", "color"),
    Output("similarity-on-off-indicator", "label"),
    Input("exit-similar-unsupervised", "n_clicks"),
    Input({"base_id": "file-manager", "name": "total-num-data-points"}, "data"),
    Input("button-hide", "n_clicks"),
    Input("button-sort", "n_clicks"),
    State("similarity-on-off-indicator", "color"),
)
def display_indicator_off(n_clicks, num_data_points, hide, sort, current_color):
    """
    This callback controls the light indicator in the DataClinic tab, which indicates whether the
    similarity-based image display is ON or OFF
    Args:
        n_clicks:        The button "Exit Similar Images" triggers this callback
        num_data_points: Total number of data points
        hide:            Hide button
        sort:            Sort button
        current_color:   Current indicator color
    Returns:
        color:           Indicator color
        label:           Indicator label
    """
    if current_color == "#596D4E":
        raise PreventUpdate
    file_path = ".current_image_order.hdf5"
    if os.path.exists(file_path):
        os.remove(file_path)
    return "#596D4E", "Find Similar Images: OFF"


@callback(
    Output("probability-collapse", "is_open"),
    Output("similarity-collapse", "is_open"),
    Output("label-buttons-collapse", "is_open"),
    Output("goto-webpage-collapse", "is_open"),
    Output("goto-webpage", "children"),
    Output("previous-tab", "data"),
    Input("tab-group", "value"),
    State("previous-tab", "data"),
)
def toggle_tabs_collapse(tab_value, previous_tab):
    """
    This callback toggles the tabs according to the selected labeling method
    """
    keys = ["manual", "probability", "similarity"]
    tabs = {key: False for key in keys}
    tabs[tab_value] = True
    if tab_value == "similarity":
        tabs["manual"] = True
    show_label_buttons = True
    goto_webpage = {"manual": False, "probability": True, "similarity": True}
    button_name = "Go to MLCoach"
    if tab_value == "similarity":
        button_name = "Go to DataClinic"
    if not previous_tab:
        previous_tab = ["init", tab_value]
    else:
        previous_tab.append(tab_value)
    return (
        tabs["probability"],
        tabs["similarity"],
        show_label_buttons,
        goto_webpage[tab_value],
        button_name,
        previous_tab,
    )


@callback(
    Output("sidebar-offcanvas", "is_open", allow_duplicate=True),
    Output("main-display", "style"),
    Input("sidebar-view", "n_clicks"),
    State("sidebar-offcanvas", "is_open"),
    prevent_initial_call=True,
)
def toggle_sidebar(n_clicks, is_open):
    if is_open:
        style = {"width": "80%", "margin": "0 auto"}
    else:
        style = {"padding": "0px 10px 0px 510px", "width": "100%"}
    return not is_open, style
