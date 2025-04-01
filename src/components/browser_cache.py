import plotly.express as px
from dash import dcc, html

from src.utils.data_utils import compress_dict


def browser_cache(mlcoach_url, data_clinic_url):
    browser_cache = html.Div(
        id="no-display",
        children=[
            dcc.Store(
                id="labels-dict",
                data=compress_dict({"labels_dict": {}, "labels_list": []}),
            ),
            dcc.Store(id="image-order", data=[]),
            dcc.Store(id="del-label", data=-1),
            dcc.Store(id="dummy1", data=0),
            dcc.Store(id="previous-tab", data=["init"]),
            dcc.Store(id="color-cycle", data=px.colors.qualitative.Light24),
            dcc.Store(id="mlcoach-url", data=mlcoach_url),
            dcc.Store(id="data-clinic-url", data=data_clinic_url),
            dcc.Store(
                id="label-dict-per-page",
                data={},
            ),
            dcc.Store(id="project-name", data=""),
        ],
    )
    return browser_cache
