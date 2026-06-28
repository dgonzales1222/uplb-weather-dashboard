"""Shared UI helpers for the Dash app — the "Editorial" UPLB design.

Header (brand + nav pills + dark toggle), footer (campus photo + contact + logos),
cards, the feels-like danger gauge, KPI/metric cards, and the shared Plotly style.
Markup uses the class names defined in assets/style.css.
"""
import dash
from dash import dcc, html

# ----------------------------------------------------------------------------
# Brand palette (kept in sync with assets/style.css)
# ----------------------------------------------------------------------------
MAROON = "#8A1538"
GOLD = "#F2A900"
GOLD_INK = "#B6831C"
GREEN = "#0E6021"
ORANGE = "#EC8A3A"
RED = "#C13F2C"
BLUE = "#5F9CD2"
PURPLE = "#7A5BA6"
TEAL = "#4FA37C"
INK = "#1D1F24"
MUTED = "#6B7280"
BORDER = "#E6E9EF"
GRID = "#EFF2F7"
SURFACE = "#FFFFFF"

UI_FONT = "Avenir, 'Nunito Sans', system-ui, sans-serif"
DISPLAY_FONT = "Spectral, Optima, Georgia, serif"

# PAGASA danger-band colors (green -> gold -> orange -> red -> maroon).
BAND_COLORS = {
    "Not hazardous": GREEN,
    "Caution": GOLD,
    "Extreme Caution": ORANGE,
    "Danger": RED,
    "Extreme Danger": MAROON,
}


# ----------------------------------------------------------------------------
# Shell: header + footer
# ----------------------------------------------------------------------------
def header():
    """Sticky brand header: UPLB seal + wordmark, dashboard title, nav pills, dark toggle.

    The nav pills are filled by a callback (see app.py) so the active page is
    highlighted; `nav-pills` is the container it targets.
    """
    return html.Header(className="hdr", children=[
        html.Div(className="hdr-inner", children=[
            html.A(href="/", className="brand", children=[
                html.Img(src="/assets/uplb-white.png", className="brand-seal", alt="UPLB"),
                html.Div(className="brand-div"),
                html.Div(className="brand-title", children=[
                    html.Span("UPLB-NAS ", className="accent"), "Weather Dashboard",
                ]),
            ]),
            html.Div(className="hdr-spacer"),
            html.Nav(id="nav-pills", className="nav-pills2"),
            html.Button("☾", id="theme-toggle", className="theme-toggle",
                        title="Toggle dark mode", n_clicks=0),
        ]),
    ])


def nav_links(pathname):
    """Nav pills built from the page registry; the current page gets `.active`."""
    pages = sorted(dash.page_registry.values(), key=lambda p: p.get("order", 99))
    links = []
    for p in pages:
        rel = p["relative_path"]
        active = (pathname or "/").rstrip("/") == rel.rstrip("/") or (rel == "/" and not pathname)
        cls = "nav-pill active" if active else "nav-pill"
        links.append(dcc.Link(p["name"], href=rel, className=cls))
    return links


def _fic(name):
    """Inline footer icon, drawn white via the CSS `mask` technique."""
    return html.Span(className="fic", style={"--i": f"url(/assets/icons/{name}.svg)"})


def footer():
    """Full-bleed campus-photo footer with contact details, logos, and attribution."""
    return html.Footer(className="footer", children=[
        html.Div(className="footer-bg",
                 style={"backgroundImage": "url(/assets/pili_drive.jpg)"}),
        html.Div(className="footer-overlay"),
        html.Div(className="footer-inner", children=[
            html.Div("UPLB Agrometeorology, Bio-structures & Environment Engineering Division",
                     className="footer-title"),
            html.Div("University of the Philippines Los Baños, IABE Complex", className="footer-line"),
            html.Div("Drive, Los Baños, 4031, Laguna, Philippines", className="footer-line"),
            html.Div(className="footer-contact", children=[
                html.Span([_fic("phone"), "+63 998 864 4258"]),
                html.Span([_fic("mail"), "abseed.iabe.uplb@up.edu.ph"]),
            ]),
            html.A([_fic("facebook"), "Follow us on Facebook"],
                   href="https://www.facebook.com/ABSEEDOfficial",
                   target="_blank", rel="noopener noreferrer",
                   className="glass-btn fb-btn"),
            html.Div(className="footer-logos", children=[
                html.Img(src="/assets/uplb-white.png", className="footer-word", alt="UPLB"),
                html.Img(src="/assets/iabe.jpg", className="footer-badge", alt="IABE"),
                html.Img(src="/assets/abseed.png", className="footer-badge", alt="ABSEED"),
            ]),
            html.Div(className="footer-fine", children=[
                html.Div("Data: Open-Meteo (ERA5) · Heat index: U.S. NWS formula · "
                         "Danger bands: PAGASA · Representative stand-in for the UPLB-NAS record."),
                html.Div("Danilo III O. Gonzales · MS Green Data Science, ISA–ULisboa",
                         className="row2"),
            ]),
        ]),
    ])


# ----------------------------------------------------------------------------
# Building blocks
# ----------------------------------------------------------------------------
def eyebrow(text):
    return html.Div(text, className="eyebrow")


def section_head(title):
    return html.Div(className="section-head", children=[
        html.H2(title, className="h2"), html.Div(className="rule"),
    ])


def card(*children, title=None, subtitle=None, className="", **kwargs):
    """A surface card; optional serif title + sub line."""
    head = []
    if title is not None:
        head.append(html.Div(title, className="card-title"))
    if subtitle is not None:
        head.append(html.Div(subtitle, className="card-sub"))
    cls = ("card2 " + className).strip()
    return html.Div(className=cls, children=head + list(children), **kwargs)


def metric_card(label, value, unit="", delta=None, delta_dir="flat"):
    """Latest-readings tile: small-caps label, serif value, unit, signed delta."""
    body = [
        html.Div(label, className="metric2-label"),
        html.Div(className="metric2-val", children=[
            html.Span(value, className="metric2-value"),
            html.Span(unit, className="metric2-unit") if unit else None,
        ]),
    ]
    if delta is not None:
        arrow = {"up": "▲ ", "down": "▼ ", "flat": ""}[delta_dir]
        body.append(html.Div(arrow + delta, className=f"metric2-delta {delta_dir}"))
    else:
        body.append(html.Div("—", className="metric2-delta flat"))
    return html.Div(body, className="metric2")


def kpi_card(label, value, sub="", accent=False):
    return html.Div(className="kpi", children=[
        html.Div(label, className="kpi-label"),
        html.Div(value, className="kpi-value accent" if accent else "kpi-value"),
        html.Div(sub, className="kpi-sub") if sub else None,
    ])


def band_badge(band):
    """The feels-like danger pill, colored by PAGASA band."""
    return html.Span(band, className="danger-pill",
                     style={"background": BAND_COLORS.get(band, MAROON)})


# Gauge domain and segment boundaries (PAGASA thresholds 27/33/42/52).
_GAUGE_LO, _GAUGE_HI = 20.0, 56.0
_GAUGE_STOPS = [20, 27, 33, 42, 52, 56]
_GAUGE_TICKS = [27, 33, 42, 52]
_GAUGE_SEG_COLORS = [GREEN, GOLD, ORANGE, RED, MAROON]


def _gpct(v):
    v = min(max(float(v), _GAUGE_LO), _GAUGE_HI)
    return (v - _GAUGE_LO) / (_GAUGE_HI - _GAUGE_LO) * 100.0


def gauge(value):
    """Horizontal danger gauge: 5 PAGASA segments + a marker at `value`."""
    segs = [
        html.Div(className="gauge-seg",
                 style={"width": f"{(_GAUGE_STOPS[i+1]-_GAUGE_STOPS[i])/(_GAUGE_HI-_GAUGE_LO)*100:.3f}%",
                        "background": c})
        for i, c in enumerate(_GAUGE_SEG_COLORS)
    ]
    marker = html.Div(className="gauge-marker", style={"left": f"{_gpct(value):.2f}%"}, children=[
        html.Div(className="flag"), html.Div(className="pin"),
    ])
    ticks = [html.Div(f"{t}", className="gauge-tick", style={"left": f"{_gpct(t):.2f}%"})
             for t in _GAUGE_TICKS]
    return html.Div(className="gauge", children=[
        html.Div(className="gauge-track", children=[html.Div(segs, className="gauge-bar"), marker]),
        html.Div(ticks, className="gauge-ticks"),
    ])


# Map a coarse daily condition to one of the weather SVGs.
def weather_icon(precipitation, humidity):
    if precipitation >= 12:
        name, label = "pouring", "Pouring"
    elif precipitation >= 3:
        name, label = "rainy", "Rainy"
    elif precipitation > 0:
        name, label = "partly-rainy", "Light rain"
    elif humidity >= 80:
        name, label = "partly-cloudy", "Partly cloudy"
    elif humidity >= 65:
        name, label = "cloudy", "Cloudy"
    else:
        name, label = "sunny", "Sunny"
    return html.Div(className="wx", children=[
        html.Div(className="wx-icon", style={"--icon": f"url(/assets/weather/{name}.svg)"}),
        html.Div(label.upper(), className="wx-label"),
    ])


# ----------------------------------------------------------------------------
# Plotly styling
# ----------------------------------------------------------------------------
def shade_bands(fig, bands, lo_clamp=10.0, hi_clamp=60.0):
    """Shade PAGASA danger zones as horizontal regions (heat-index trend)."""
    for lo, hi, label in bands:
        if label == "Not hazardous":
            continue
        fig.add_hrect(y0=max(lo, lo_clamp), y1=min(hi, hi_clamp),
                      fillcolor=BAND_COLORS.get(label, "#94a3b8"),
                      opacity=0.12, line_width=0, layer="below")
    return fig


def style_fig(fig, height: int = 320):
    """Apply the editorial chart style (serif titles, brand grid) and return it."""
    has_title = bool(getattr(fig.layout.title, "text", None))
    fig.update_layout(
        template="plotly_white", height=height,
        margin=dict(l=12, r=12, t=44 if has_title else 14, b=12),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        font=dict(family=UI_FONT, size=12, color=INK),
        title=dict(font=dict(family=DISPLAY_FONT, size=17, color=INK), x=0, xanchor="left"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=1, xanchor="right",
                    font=dict(family=UI_FONT, size=11), bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="rgba(255,255,255,0.92)", font=dict(family=UI_FONT)),
    )
    fig.update_xaxes(showgrid=False, linecolor="rgba(120,110,90,.25)", tickcolor="rgba(120,110,90,.25)")
    fig.update_yaxes(gridcolor="rgba(120,110,90,.16)", zeroline=False)
    return fig


CHART_CONFIG = {"displayModeBar": False}
