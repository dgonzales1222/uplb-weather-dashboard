"""Dash web app — entry point (the "Editorial" UPLB design).

Single styled dashboard: a sticky brand header with nav pills + dark toggle, the
page container, and a campus-photo footer. Reads only from data/weather.db via
src/db/queries.py.

Run with:  python -m src.dashapp.app   (http://localhost:8050)
"""
import sys
from pathlib import Path

# Allow `python src/dashapp/app.py` too by putting the project root on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import dash_bootstrap_components as dbc
from dash import Dash, Input, Output, callback, dcc, html, page_container

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
    dcc.Location(id="url"),
    theme.header(),
    html.Main(html.Div(page_container, className="page")),
    theme.footer(),
])


@callback(Output("nav-pills", "children"), Input("url", "pathname"))
def _nav(pathname):
    return theme.nav_links(pathname)


# Dark-mode toggle: flip the `dark` class on <html>; persist in localStorage.
app.clientside_callback(
    """
    function(n) {
        const root = document.documentElement;
        if (n) { root.classList.toggle('dark'); }
        try { localStorage.setItem('uplb-dark', root.classList.contains('dark') ? '1' : '0'); } catch (e) {}
        return root.classList.contains('dark') ? '☀' : '☾';
    }
    """,
    Output("theme-toggle", "children"),
    Input("theme-toggle", "n_clicks"),
)


if __name__ == "__main__":
    app.run(debug=False, port=8050)
