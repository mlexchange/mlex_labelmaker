import dash_bootstrap_components as dbc
from dash import dcc, html
from mlex_utils.dash_utils.components_bootstrap.component_utils import (
    DbcControlItem as ControlItem,
)

from src.utils.mask_utils import get_mask_options


def data_transformations():
    display_settings = [
        ControlItem(
            "",
            "empty-title-log-transform",
            dbc.Switch(
                id="log-transform",
                value=False,
                label="Log Transform",
            ),
        ),
        html.P(),
        ControlItem(
            "Min-Max Percentile",
            "min-max-percentile-title",
            dcc.RangeSlider(
                id="min-max-percentile",
                min=0,
                max=100,
                tooltip={
                    "placement": "bottom",
                    "always_visible": True,
                },
                value=[0, 100],
            ),
        ),
        html.P(),
        ControlItem(
            "Mask Selection",
            "mask-dropdown-title",
            dbc.Select(
                id="mask-dropdown",
                options=get_mask_options(),
                value="None",
            ),
        ),
    ]
    return display_settings
