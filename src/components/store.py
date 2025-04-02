import dash_bootstrap_components as dbc
from dash import dcc, html


def store_options():
    store_options = html.Div(
        [
            dbc.Button(
                "Load Labels from Server",
                id="button-load-tiled",
                outline="True",
                color="success",
                size="sm",
                style={"width": "100%", "margin-bottom": "4px"},
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Labeling versions")),
                    dbc.ModalBody(dcc.Dropdown(id="event-id")),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "LOAD",
                                id="confirm-load-tiled",
                                color="primary",
                                outline=False,
                                className="ms-auto",
                                n_clicks=0,
                            )
                        ]
                    ),
                ],
                id="modal-load-tiled",
                is_open=False,
            ),
            dbc.Button(
                "Save Labels to Server",
                id="button-save-tiled",
                outline="True",
                color="primary",
                size="sm",
                style={"width": "100%", "margin-bottom": "4px"},
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Tagger ID")),
                    dbc.ModalBody(
                        [
                            dbc.Label("Entry tagger ID:"),
                            dbc.Input(id="tagger-id", type="text"),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "SAVE",
                                id="confirm-save-tiled",
                                color="primary",
                                outline=False,
                                className="ms-auto",
                                n_clicks=0,
                            )
                        ]
                    ),
                ],
                id="modal-save-tiled",
                is_open=False,
            ),
            dbc.Button(
                "Download Labels as ZIP",
                id="button-save-zip",
                outline="True",
                color="primary",
                size="sm",
                style={"width": "100%", "margin-bottom": "4px"},
            ),
            dbc.Button(
                "Download Labels as Table",
                id="button-save-table",
                outline="True",
                color="primary",
                size="sm",
                style={"width": "100%"},
            ),
            dcc.Download(id="download-out"),
            dbc.Modal(
                [
                    dbc.ModalBody(id="storage-body-modal"),
                    dbc.ModalFooter(dbc.Button("OK", id="close-storage-modal")),
                ],
                id="storage-modal",
                is_open=False,
                scrollable=True,
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(id="store-progress-title")),
                    dbc.ModalBody(dbc.Progress(id="store-progress")),
                ],
                id="modal-store-progress",
                is_open=False,
            ),
        ]
    )
    return store_options
