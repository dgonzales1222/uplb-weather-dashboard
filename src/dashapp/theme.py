"""Shared UI helpers for the Dash app — header (title + logo slots), sidebar nav,
metric cards, PAGASA badge, and the shared Plotly chart style.
"""
import dash
import dash_bootstrap_components as dbc
from dash import html

# PAGASA danger-band colors for the feels-like badge.
BAND_COLORS = {
    "Not hazardous": "#64748b", "Caution": "#ca8a04",
    "Extreme Caution": "#f59e0b", "Danger": "#ef4444",
    "Extreme Danger": "#b91c1c",
}


def header(title, subtitle="", logos=None):
    """Top header banner: title/subtitle on the left, a logo strip on the right.

    `logos` is a list of asset URLs (e.g. "/assets/uplb.png"), rendered left→right.
    """
    imgs = [html.Img(src=src, className="logo-img") for src in (logos or [])]
    return html.Div(className="app-header", children=[
        html.Div(className="row", children=[
            html.Div(className="txt", children=[
                html.Div(title, className="ttl"),
                html.Div(subtitle, className="sub"),
            ]),
            html.Div(imgs, className="logos"),
        ]),
    ])


def sidebar():
    """Left navigation menu built from the registered pages."""
    links = [
        dbc.NavLink(p["name"], href=p["relative_path"], active="exact")
        for p in sorted(dash.page_registry.values(), key=lambda p: p.get("order", 99))
    ]
    return html.Div(className="sidebar", children=[
        html.Div("Menu", className="sidebar-title"),
        dbc.Nav(links, vertical=True, pills=True),
    ])


def metric_card(label, value, delta=None):
    body = [html.Div(label, className="metric-label"), html.Div(value, className="metric-value")]
    if delta is not None:
        body.append(html.Div(delta, className="metric-delta"))
    return dbc.Card(dbc.CardBody(body), className="metric-card")


def band_badge(band):
    return html.Span(band, className="band-badge",
                     style={"background": BAND_COLORS.get(band, "#64748b")})


def shade_bands(fig, bands, lo_clamp=10.0, hi_clamp=60.0):
    """Shade danger-band zones as horizontal regions (for the heat-index trend).

    `bands` is a sequence of (lower, upper, label) in °C (e.g. heat_index.PAGASA_BANDS).
    Infinite bounds are clamped to a sensible heat-index range.
    """
    for lo, hi, label in bands:
        if label == "Not hazardous":
            continue
        fig.add_hrect(y0=max(lo, lo_clamp), y1=min(hi, hi_clamp),
                      fillcolor=BAND_COLORS.get(label, "#94a3b8"),
                      opacity=0.13, line_width=0, layer="below")
    return fig


def style_fig(fig, height: int = 320):
    """Apply the minimal, card-friendly chart style and return the figure."""
    fig.update_layout(
        template="plotly_white", height=height,
        margin=dict(l=10, r=10, t=44, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified", font=dict(size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=1, xanchor="right"),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#eef2f6", zeroline=False)
    return fig


CHART_CONFIG = {"displayModeBar": False}
