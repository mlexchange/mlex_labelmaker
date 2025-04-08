import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import dcc, html
from dash_extensions import EventListener
from dash_iconify import DashIconify
from mlex_utils.dash_utils.components_bootstrap.component_utils import (
    DbcControlItem as ControlItem,
)

from src.utils.plot_utils import create_label_component


def label_method():
    label_method = html.Div(
        [
            html.Div(
                [
                    dbc.RadioItems(
                        id="tab-group",
                        className="btn-group",
                        inputClassName="btn-check",
                        labelClassName="btn btn-outline-primary",
                        labelCheckedClassName="active",
                        labelStyle={
                            "font-size": "13px",
                            "margin": "1px",
                            "width": "100%",  # "width": "85px",
                        },
                        options=[
                            {"label": "Manual", "value": "manual"},
                            {"label": "Similarity", "value": "similarity"},
                            {"label": "Probability", "value": "probability"},
                        ],
                        style={"width": "100%"},
                        value="manual",
                    )
                ],
                className="radio-group",
                style={"font-size": "0.5px", "margin-bottom": "10px"},
            ),
            # Labeling with Probabilities
            dbc.Collapse(
                children=[
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Button(
                                    "Go to MLCoach",
                                    id="goto-webpage",
                                    outline="True",
                                    color="primary",
                                    size="sm",
                                    n_clicks=0,
                                    style={
                                        "width": "100%",
                                        "margin-bottom": "1rem",
                                        "margin-top": "0.5rem",
                                    },
                                ),
                                width=11,
                                style={"margin-right": "2%", "width": "90%"},
                            ),
                            dbc.Col(
                                dbc.Button(
                                    className="fa fa-question",
                                    id="tab-help-button",
                                    outline="True",
                                    color="primary",
                                    size="sm",
                                    style={
                                        "width": "100%",
                                        "margin-bottom": "1rem",
                                        "margin-top": "0.5rem",
                                    },
                                ),
                                width=1,
                                style={"width": "8%"},
                            ),
                        ],
                        className="g-0",
                    )
                ],
                id="goto-webpage-collapse",
                is_open=False,
            ),
            # manual tab is default button group
            dbc.Collapse(
                children=html.Div(
                    id="label-buttons",
                    children=create_label_component(),
                    style={"margin-bottom": "0.5rem"},
                ),
                id="label-buttons-collapse",
                is_open=False,
            ),
            # Labeling with Probabilities
            dbc.Collapse(
                children=[
                    ControlItem(
                        "Trained models:",
                        "prob-model-title",
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Select(
                                            id="probability-model-list",
                                            options=[],
                                            value=None,
                                        ),
                                        width=10,
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            DashIconify(
                                                icon="mdi:refresh-circle",
                                                width=20,
                                                style={"display": "block"},
                                            ),
                                            id="probability-model-refresh",
                                            color="secondary",
                                            size="sm",
                                            className="rounded-circle",
                                            style={
                                                "aspectRatio": "1 / 1",
                                                "paddingLeft": "1px",
                                                "paddingRight": "1px",
                                                "paddingTop": "1px",
                                                "paddingBottom": "1px",
                                            },
                                        ),
                                        className="d-flex justify-content-center align-items-center",
                                        width=2,
                                    ),
                                ],
                                className="g-1",
                            ),
                        ],
                    ),
                    html.P(),
                    ControlItem(
                        "Label to Assign:",
                        "prob-label-name-title",
                        dbc.Select(
                            id="probability-label-name",
                            options=[],
                            value=None,
                        ),
                    ),
                    html.P(),
                    ControlItem(
                        "Probability Threshold:",
                        "prob-threshold-title",
                        dcc.Slider(
                            id="probability-threshold",
                            min=0,
                            max=100,
                            value=51,
                            tooltip={"placement": "top", "always_visible": True},
                            marks={0: "0", 25: "25", 50: "50", 75: "75", 100: "100"},
                        ),
                    ),
                    dbc.Button(
                        "Label with Threshold",
                        id="probability-label",
                        outline="True",
                        color="primary",
                        size="sm",
                        style={"width": "100%", "margin-top": "20px"},
                    ),
                ],
                id="probability-collapse",
                is_open=False,
            ),
            # Labeling with similarity-based search
            dbc.Collapse(
                children=[
                    ControlItem(
                        "Trained models:",
                        "similarity-model-title",
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Select(
                                            id="similarity-model-list",
                                            options=[],
                                            value=None,
                                        ),
                                        width=10,
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            DashIconify(
                                                icon="mdi:refresh-circle",
                                                width=20,
                                                style={"display": "block"},
                                            ),
                                            id="similarity-model-refresh",
                                            color="secondary",
                                            size="sm",
                                            className="rounded-circle",
                                            style={
                                                "aspectRatio": "1 / 1",
                                                "paddingLeft": "1px",
                                                "paddingRight": "1px",
                                                "paddingTop": "1px",
                                                "paddingBottom": "1px",
                                            },
                                        ),
                                        className="d-flex justify-content-center align-items-center",
                                        width=2,
                                    ),
                                ],
                                className="g-1",
                            ),
                        ],
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Button(
                                    "Find Similar Images",
                                    id="find-similar-unsupervised",
                                    outline="True",
                                    color="primary",
                                    size="sm",
                                    style={"width": "100%", "margin-top": "20px"},
                                )
                            ),
                            dbc.Col(
                                dbc.Button(
                                    "Stop Find Similar Images",
                                    id="exit-similar-unsupervised",
                                    outline="True",
                                    color="primary",
                                    size="sm",
                                    style={"width": "100%", "margin-top": "20px"},
                                )
                            ),
                        ],
                    ),
                    daq.Indicator(
                        id="similarity-on-off-indicator",
                        label="Find Similar Images: OFF",
                        color="#596D4E",
                        size=30,
                        style={"margin-top": "20px", "margin-bottom": "20px"},
                    ),
                ],
                id="similarity-collapse",
                is_open=False,
            ),
            dbc.Button(
                "Unlabel the Selected",
                id="un-label",
                className="ms-auto",
                color="danger",
                size="sm",
                outline=True,
                style={"width": "100%", "margin-bottom": "10px", "margin-top": "10px"},
            ),
            dbc.Button(
                "Unlabel All",
                id="un-label-all",
                outline="True",
                color="danger",
                size="sm",
                style={"width": "100%", "margin-bottom": "4px", "margin-top": "4px"},
            ),
            dbc.Modal(
                id="color-picker-modal",
                children=[
                    html.P(),
                    ControlItem(
                        "Label Name:",
                        "label-name-title",
                        dbc.Input(
                            id="modify-label-name",
                            value="",
                            placeholder="Type new label name",
                        ),
                        style={"width": "80%", "margin": "0px"},
                    ),
                    html.P(),
                    daq.ColorPicker(
                        id="label-color-picker",
                        label="Choose label color",
                        value=dict(hex="#119DFF"),
                    ),
                    html.P(),
                    dbc.Button(
                        "Submit", id="modify-label-button", style={"width": "100%"}
                    ),
                ],
                is_open=False,
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Warning")),
                    dbc.ModalBody(
                        id="un-label-warning",
                        children="Unsaved labels cannot be recovered after clearing data. Do \
                          you still want to proceed?",
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "YES",
                                id="confirm-un-label-all",
                                color="danger",
                                outline=False,
                                className="ms-auto",
                                n_clicks=0,
                            ),
                        ]
                    ),
                ],
                id="modal-un-label",
                is_open=False,
                style={"color": "red"},
            ),
            dbc.Modal(
                id="modal-help",
                children=[
                    dbc.ModalHeader(dbc.ModalTitle("Help")),
                    dbc.ModalBody(id="help-body"),
                ],
            ),
            EventListener(
                events=[
                    {
                        "event": "keydown",
                        "props": ["key", "ctrlKey", "timeStamp"],
                        "repeat": True,
                    }
                ],
                id="keybind-event-listener",
                logging=True,
            ),
        ]
    )
    return label_method
