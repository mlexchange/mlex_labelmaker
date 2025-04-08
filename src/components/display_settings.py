import dash_bootstrap_components as dbc
from dash import dcc, html
from mlex_utils.dash_utils.components_bootstrap.component_utils import (
    DbcControlItem as ControlItem,
)


def display_settings():
    display_settings = html.Div(
        [
            ControlItem(
                "Number of Columns:",
                "num-cols-title",
                dcc.Slider(1, 6, 1, value=6, id="thumbnail-num-cols"),
            ),
            html.P(),
            ControlItem(
                "Number of Rows:",
                "num-rows-title",
                dcc.Slider(1, 6, 1, value=3, id="thumbnail-num-rows"),
            ),
            dbc.Button(
                "Sort",
                id="button-sort",
                outline="True",
                color="primary",
                size="sm",
                n_clicks=0,
                style={"width": "100%", "margin-top": "20px", "margin-bottom": "4px"},
            ),
            dbc.Tooltip(
                "Sort images according to assigned label",
                target="button-sort",
                placement="top",
            ),
            dbc.Button(
                "Hide",
                id="button-hide",
                outline="True",
                color="primary",
                size="sm",
                n_clicks=0,
                style={"width": "100%", "margin-bottom": "4px"},
            ),
            dbc.Tooltip(
                "Hide/unhide labeled images", target="button-hide", placement="top"
            ),
        ]
    )
    return display_settings
