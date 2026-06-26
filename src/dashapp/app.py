"""Dash web app — entry point (replaces the Streamlit app).

Multipage shell: a top header (title + logo slots), a left sidebar nav menu, and
the page container. Reads only from data/weather.db via src/db/queries.py.

Run with:  python -m src.dashapp.app   (http://localhost:8050)
"""
import sys
from pathlib import Path

# Allow `python src/dashapp/app.py` too by putting the project root on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import dash_bootstrap_components as dbc
from dash import Dash, html, page_container

import config
from src.dashapp import theme

_HERE = Path(__file__).resolve().parent

app = Dash(
    __name__,
    use_pages=True,
    pages_folder=str(_HERE / "pages"),
    assets_folder=str(_HERE / "assets"),
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True,
    title="UPLB-NAS Weather Dashboard",
)
server = app.server  # for gunicorn / deployment

app.layout = html.Div([
    theme.header(
        "🌡️ UPLB-NAS Weather Data Dashboard",
        f"Open-Meteo ERA5 stand-in · Los Baños, Laguna · {config.LAT}, {config.LON}",
    ),
    html.Div(className="body", children=[
        theme.sidebar(),
        html.Div(page_container, className="content"),
    ]),
])


if __name__ == "__main__":
    app.run(debug=False, port=8050)
