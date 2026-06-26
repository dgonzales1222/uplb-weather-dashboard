"""Climate Insights (Heat Index) page (Dash) — Phase 5.

Applies the heat-index module across the full record: a multi-year trend with
PAGASA/NWS danger bands, a calendar heatmap of daily heat index, and the annual
count of days above 41 °C.
"""
import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from src.dashapp import data, theme
from src.features import heat_index

dash.register_page(__name__, path="/climate-insights", name="Climate Insights", order=1)

DANGER_C = 41.0  # README metric: days exceeding a 41 °C heat index


def _bands(system):
    return heat_index.NWS_BANDS if system == "NWS" else heat_index.PAGASA_BANDS


def _trend_fig(system):
    hid = data.heat_index_daily()
    annual = hid.groupby(hid.index.year)["hi_c"].mean()
    years = annual.index.to_numpy()
    vals = annual.to_numpy()

    fig = go.Figure()
    theme.shade_bands(fig, _bands(system))
    fig.add_trace(go.Scatter(x=years, y=vals, name="Annual mean HI",
                             mode="lines+markers", line=dict(color="#b91c1c", width=2.5)))
    slope, intercept = np.polyfit(years, vals, 1)
    fig.add_trace(go.Scatter(x=years, y=slope * years + intercept, name="Trend",
                             mode="lines", line=dict(color="#334155", dash="dash")))
    fig.update_layout(title=f"Annual mean heat index ({system} bands)",
                      yaxis_title="Heat index (°C)")
    fig.update_yaxes(range=[vals.min() - 2, vals.max() + 6])
    return theme.style_fig(fig, height=360)


def _heatmap_fig():
    hid = data.heat_index_daily().copy()
    hid["doy"] = hid.index.dayofyear
    hid["yr"] = hid.index.year
    pivot = hid.pivot_table(index="yr", columns="doy", values="hi_c")
    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns, y=pivot.index,
        colorscale="YlOrRd", colorbar=dict(title="HI °C"),
    ))
    fig.update_layout(title="Daily heat index — calendar heatmap",
                      xaxis_title="Day of year", yaxis_title="Year")
    fig = theme.style_fig(fig, height=430)
    fig.update_layout(hovermode="closest")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)")
    return fig


def _counter_fig():
    hid = data.heat_index_daily()
    counts = (hid["hi_c"] > DANGER_C).groupby(hid.index.year).sum()
    fig = go.Figure(go.Bar(x=counts.index, y=counts.to_numpy(), marker_color="#ef4444"))
    fig.update_layout(title=f"Days with heat index > {DANGER_C:.0f} °C", yaxis_title="Days")
    return theme.style_fig(fig, height=320)


def _kpis():
    hid = data.heat_index_daily()
    annual_mean = hid.groupby(hid.index.year)["hi_c"].mean()
    cards = [
        ("Mean heat index", f"{hid['hi_c'].mean():.1f} °C"),
        ("Hottest year (mean HI)", str(int(annual_mean.idxmax()))),
        (f"Days > {DANGER_C:.0f} °C", f"{int((hid['hi_c'] > DANGER_C).sum()):,}"),
        ("Danger+ share", f"{100 * hid['band'].isin(['Danger', 'Extreme Danger']).mean():.0f}%"),
    ]
    return dbc.Row([dbc.Col(theme.metric_card(l, v), md=3, sm=6) for l, v in cards],
                   className="g-2")


def layout(**_):
    hid = data.heat_index_daily()
    if hid.empty:
        return dbc.Alert("Database not found. Build it first:  python -m src.data.ingest",
                         color="warning")
    y_min, y_max = int(hid.index.year.min()), int(hid.index.year.max())
    return html.Div([
        dbc.Card(dbc.CardBody([
            html.H5("📈 Climate Insights — Heat Index"),
            html.Div(
                f"Daily heat index from daily max temperature + mean relative humidity, "
                f"{y_min}–{y_max}. Note: pairing Tmax with mean RH tends to OVERESTIMATE the "
                f"heat index (humidity is lowest at peak heat).",
                className="muted"),
            _kpis(),
        ])),
        dbc.Card(dbc.CardBody([
            html.Div(className="d-flex justify-content-between align-items-center mb-2", children=[
                html.H5("Multi-year trend", className="mb-0"),
                dcc.RadioItems(id="ci-bands", options=["PAGASA", "NWS"], value="PAGASA",
                               inline=True, inputClassName="me-1", labelClassName="me-3"),
            ]),
            dcc.Graph(id="ci-trend", config=theme.CHART_CONFIG),
        ])),
        dbc.Card(dbc.CardBody([
            html.H5("Calendar heatmap"),
            dcc.Graph(figure=_heatmap_fig(), config=theme.CHART_CONFIG),
        ])),
        dbc.Card(dbc.CardBody([
            html.H5("Dangerous days per year"),
            dcc.Graph(figure=_counter_fig(), config=theme.CHART_CONFIG),
        ])),
    ])


@callback(Output("ci-trend", "figure"), Input("ci-bands", "value"))
def update_trend(system):
    return _trend_fig(system)
