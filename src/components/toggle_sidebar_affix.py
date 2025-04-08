import dash_bootstrap_components as dbc
from dash import html
from dash_iconify import DashIconify


def create_show_sidebar_affix():
    return html.Div(
        [
            dbc.Button(
                DashIconify(icon="circum:settings", width=20),
                id="sidebar-view",
                size="sm",
                color="secondary",
                className="rounded-circle",
                style={"aspectRatio": "1 / 1"},
            ),
            dbc.Tooltip(
                "Toggle sidebar",
                target="sidebar-view",
                placement="top",
            ),
        ],
        style={
            "position": "fixed",
            "bottom": "60px",
            "right": "10px",
            "zIndex": 9999,  # Note: zIndex is unitless
            "opacity": "0.8",
        },
    )
