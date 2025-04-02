import os
import time

import dash
from dash import Input, Output, State, dcc
from file_manager.data_project import DataProject
from flask import request
from werkzeug.middleware.profiler import ProfilerMiddleware

from src.app_layout import (  # noqa: F401
    TILED_KEY,
    app,
    logger,
    long_callback_manager,
    server,
)
from src.callbacks.display import (  # noqa: F401;
    deselect,
    display_indicator_off,
    display_indicator_on,
    full_screen_thumbnail,
    toggle_tabs_collapse,
    update_hide_button_text,
    update_label_dict_per_page,
    update_output,
    update_probabilities,
    update_rows,
)
from src.callbacks.display_order import (  # noqa: F401
    disable_buttons,
    go_to_first_page,
    go_to_last_page,
    go_to_next_page,
    go_to_prev_page,
    go_to_users_input,
    undo_sort_or_hide_labeled_images,
    update_image_order,
)
from src.callbacks.help import toggle_help_modal  # noqa: F401
from src.callbacks.manage_labels import (  # noqa: F401
    add_new_label,
    delete_label,
    label_selected_thumbnails,
    label_selected_thumbnails_key_binds,
    label_selected_thumbnails_new_dataset,
    label_selected_thumbnails_probability,
    load_from_tiled_modal,
    load_labels_from_probabilities,
    modify_label,
    toggle_color_picker_modal,
    unlabel_selected_thumbnails,
    update_labeling_progress,
)
from src.callbacks.update_models import update_trained_model_list  # noqa: F401
from src.callbacks.warning import toggle_modal_unlabel_warning  # noqa: F401
from src.labels import Labels
from src.utils.data_utils import compress_dict, decompress_dict
from src.utils.plot_utils import create_label_component

APP_PORT = os.getenv("APP_PORT", 8057)
APP_HOST = os.getenv("APP_HOST", "127.0.0.1")


app.clientside_callback(
    """
    function(n_clicks, tab_value, mlcoach_url, data_clinic_url) {
        if (tab_value == 'probability') {
            window.open(mlcoach_url);
        } else if (tab_value == 'similarity') {
            window.open(data_clinic_url);
        }
        return '';
    }
    """,
    Output("dummy1", "data"),
    Input("goto-webpage", "n_clicks"),
    State("tab-group", "value"),
    State("mlcoach-url", "data"),
    State("data-clinic-url", "data"),
    prevent_initial_call=True,
)


@app.long_callback(
    Output("storage-modal", "is_open"),
    Output("storage-body-modal", "children"),
    Input("confirm-save-tiled", "n_clicks"),
    State({"base_id": "file-manager", "name": "data-project-dict"}, "data"),
    State("labels-dict", "data"),
    State("tagger-id", "value"),
    State("project-name", "data"),
    manager=long_callback_manager,
    prevent_initial_call=True,
    running=[
        (Output("modal-store-progress", "is_open"), True, False),
        (Output("store-progress-title", "children"), "Storing labels to server...", ""),
    ],
    progress=[Output("store-progress", "value")],
)
def save_labels_to_tiled(
    set_progress,
    button_confirm_tiled_n_clicks,
    data_project_dict,
    labels_dict,
    tagger_id,
    project_name,
):
    """
    This callback saves the labels to disk or to tiled
    Args:
        button_confirm_tiled_n_clicks: Button to confirm save to tiled
        data_project_dict:              Data project information
        labels_dict:                    Dictionary of labeled images (docker path), as follows:
                                        {filename1: [label1, label2], ...}
        tagger_id:                      ID to identify the user/tagger
        project_name:                   Name of the project
    Returns:
        storage_modal_open:             Open/closes the confirmation message
        storage_body_modal:             Confirmation message
    """
    labels_dict = decompress_dict(labels_dict)
    labels = Labels(**labels_dict)
    if sum(labels.num_imgs_per_label.values()) > 0:
        # Load data project
        data_project = DataProject.from_dict(data_project_dict, api_key=TILED_KEY)
        labels_tiled_url = labels.save_to_tiled(
            tagger_id, data_project, project_name, set_progress
        )
        return True, f"Labels stored in tiled at {labels_tiled_url}"

    return True, "No labels to save"


@app.long_callback(
    Output("label-buttons", "children", allow_duplicate=True),
    Output("labels-dict", "data", allow_duplicate=True),
    Input("confirm-load-tiled", "n_clicks"),
    State("labels-dict", "data"),
    State("event-id", "value"),
    State("color-cycle", "data"),
    State({"base_id": "file-manager", "name": "data-project-dict"}, "data"),
    State("project-name", "data"),
    prevent_initial_call=True,
    running=[
        (Output("modal-store-progress", "is_open"), True, False),
        (
            Output("store-progress-title", "children"),
            "Loading labels from server...",
            "",
        ),
    ],
    progress=[Output("store-progress", "value")],
)
def load_labels_from_tiled(
    set_progress,
    load_tiled_n_clicks,
    labels_dict,
    event_id,
    color_cycle,
    data_project_dict,
    project_name,
):
    start = time.time()
    labels_dict = decompress_dict(labels_dict)
    labels = Labels(**labels_dict)
    data_project = DataProject.from_dict(data_project_dict, api_key=TILED_KEY)
    labels.load_tiled_labels(data_project, event_id, project_name, set_progress)
    label_comp = create_label_component(labels.labels_list, color_cycle)
    logger.debug(f"Updating labels after {time.time()-start}")
    return label_comp, compress_dict(labels.to_dict())


@app.long_callback(
    Output("download-out", "data"),
    Output("storage-modal", "is_open", allow_duplicate=True),
    Output("storage-body-modal", "children", allow_duplicate=True),
    Input("button-save-zip", "n_clicks"),
    State({"base_id": "file-manager", "name": "data-project-dict"}, "data"),
    State("labels-dict", "data"),
    manager=long_callback_manager,
    prevent_initial_call=True,
    running=[
        (Output("modal-store-progress", "is_open"), True, False),
        (
            Output("store-progress-title", "children"),
            "Preparing labels for download...",
            "",
        ),
    ],
    progress=[Output("store-progress", "value")],
)
def save_labels_as_zip(
    set_progress,
    button_save_zip_n_clicks,
    data_project_dict,
    labels_dict,
):
    """
    This callback saves the labels to disk
    Args:
        button_save_zip_n_clicks:       Button to save to disk as zip
        data_project_dict:              Data project information
        labels_dict:                    Dictionary of labeled images (docker path), as follows:
                                        {filename1: [label1, label2], ...}
    Returns:
        download_out:                   Download output
        storage_modal_open:             Open/closes the confirmation message
        storage_body_modal:             Confirmation message
    """
    labels_dict = decompress_dict(labels_dict)
    labels = Labels(**labels_dict)
    if sum(labels.num_imgs_per_label.values()) > 0:
        # Load data project
        data_project = DataProject.from_dict(
            data_project_dict, set_progress=set_progress, api_key=TILED_KEY
        )

        path_save = labels.save_to_directory(data_project)
        response = "Download will start shortly"
        return (dcc.send_file(f"{path_save}.zip", filename="files.zip"), True, response)

    return dash.no_update, True, "No labels to save"


@app.long_callback(
    Output("download-out", "data", allow_duplicate=True),
    Output("storage-modal", "is_open", allow_duplicate=True),
    Output("storage-body-modal", "children", allow_duplicate=True),
    Input("button-save-table", "n_clicks"),
    State({"base_id": "file-manager", "name": "data-project-dict"}, "data"),
    State("labels-dict", "data"),
    manager=long_callback_manager,
    prevent_initial_call=True,
    running=[
        (Output("modal-store-progress", "is_open"), True, False),
        (
            Output("store-progress-title", "children"),
            "Preparing labels for download...",
            "",
        ),
    ],
    progress=[Output("store-progress", "value")],
)
def save_labels_as_table(
    set_progress,
    button_save_table_n_clicks,
    data_project_dict,
    labels_dict,
):
    """
    This callback saves the labels to disk
    Args:
        button_save_table_n_clicks:     Button to save to disk as table
        data_project_dict:              Data project information
        labels_dict:                    Dictionary of labeled images (docker path), as follows:
                                        {filename1: [label1, label2], ...}
    Returns:
        download_out:                   Download output
        storage_modal_open:             Open/closes the confirmation message
        storage_body_modal:             Confirmation message
    """
    labels_dict = decompress_dict(labels_dict)
    labels = Labels(**labels_dict)
    if sum(labels.num_imgs_per_label.values()) > 0:
        # Load data project
        data_project = DataProject.from_dict(data_project_dict, api_key=TILED_KEY)

        path_save = labels.save_to_table(data_project, set_progress)
        response = "Download will start shortly"
        return (dcc.send_file(path_save, filename="labels.csv"), True, response)

    return dash.no_update, True, "No labels to save"


@app.callback(
    Output("storage-modal", "is_open", allow_duplicate=True),
    Input("close-storage-modal", "n_clicks"),
    prevent_initial_call=True,
)
def close_storage_modal(close_modal_n_clicks):
    """
    This callback closes the storage modal
    Args:
        close_modal_n_clicks: Button to close the confirmation message
    Returns:
        storage_modal_open:  Open/closes the confirmation message
    """
    return False


@app.callback(
    Output("modal-save-tiled", "is_open", allow_duplicate=True),
    Input("button-save-tiled", "n_clicks"),
    Input("confirm-save-tiled", "n_clicks"),
    State("modal-save-tiled", "is_open"),
    prevent_initial_call=True,
)
def toggle_tiled_modal(
    button_save_tiled_n_clicks,
    button_confirm_tiled_n_clicks,
    storage_modal_open,
):
    """
    This callback toggles the tiled modal
    Args:
        button_save_tiled_n_clicks:    Button to save to tiled
        button_confirm_tiled_n_clicks: Button to confirm save to tiled
    Returns:
        storage_modal_open:             Open/closes the confirmation message
    """
    return not storage_modal_open


if __name__ == "__main__":

    profiler = os.getenv("PROFILER", None)
    if profiler == "werkzeug":
        app.server.config["PROFILE"] = True
        app.server.wsgi_app = ProfilerMiddleware(
            app.server.wsgi_app, sort_by=("cumtime", "tottime"), restrictions=[50]
        )

    elif profiler == "flask":

        @server.before_request
        def start_timer():
            request.start_time = time.time()

        @server.after_request
        def log_request(response):
            if hasattr(request, "start_time"):
                duration = time.time() - request.start_time
                logger.debug(f"Request to {request.path} took {duration:.4f} seconds")
            return response

    app.run_server(host=APP_HOST, port=APP_PORT, debug=True)
