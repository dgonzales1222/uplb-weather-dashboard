"""Climate Insights (Heat Index) page (Dash) — the "Editorial" UPLB design.

Heat-index climate record over the full series: KPI cards, a multi-year trend
with PAGASA danger bands, a calendar heatmap, the annual count of dangerous days,
and a short-term forecast with backtest accuracy. Data/figure logic is reused.
"""
import dash
import numpy as np
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from src.dashapp import data, theme
from src.features import heat_index

dash.register_page(__name__, path="/climate-insights", name="Climate Insights", order=1)

DANGER_C = 41.0  # README metric: days exceeding a 41 °C heat index


def _warming_rate(hid):
    annual = hid.groupby(hid.index.year)["hi_c"].mean()
    slope = np.polyfit(annual.index.to_numpy(), annual.to_numpy(), 1)[0]
    return slope * 10.0


def _kpis(hid):
    annual_mean = hid.groupby(hid.index.year)["hi_c"].mean()
    hottest = int(annual_mean.idxmax())
    cards = [
        theme.kpi_card("Mean heat index", f"{hid['hi_c'].mean():.1f} °C", "full record"),
        theme.kpi_card("Warming rate", f"{_warming_rate(hid):+.2f} °C", "per decade · annual-mean HI",
                       accent=True),
        theme.kpi_card(f"Days > {DANGER_C:.0f} °C", f"{int((hid['hi_c'] > DANGER_C).sum()):,}",
                       "danger threshold"),
        theme.kpi_card("Hottest year", str(hottest), f"mean HI {annual_mean.max():.1f} °C"),
    ]
    return html.Div(cards, className="kpi-row")


def _trend_fig():
    hid = data.heat_index_daily()
    annual = hid.groupby(hid.index.year)["hi_c"].mean()
    years = annual.index.to_numpy()
    vals = annual.to_numpy()

    fig = go.Figure()
    theme.shade_bands(fig, heat_index.PAGASA_BANDS)
    fig.add_trace(go.Scatter(x=years, y=vals, name="Annual mean HI",
                             mode="lines+markers",
                             line=dict(color=theme.MAROON, width=2.5, shape="spline", smoothing=0.6)))
    slope, intercept = np.polyfit(years, vals, 1)
    fig.add_trace(go.Scatter(x=years, y=slope * years + intercept, name="Trend",
                             mode="lines", line=dict(color=theme.MUTED, dash="dash")))
    fig.add_annotation(x=years[0], y=vals.max() + 4, xanchor="left", showarrow=False,
                       text=f"<b>{slope*10:+.2f}°C / decade</b>", font=dict(color=theme.MAROON, size=13))
    fig.update_layout(yaxis_title="Heat index (°C)")
    fig.update_yaxes(range=[vals.min() - 2, vals.max() + 6])
    return theme.style_fig(fig, height=380)


def _heatmap_fig():
    hid = data.heat_index_daily().copy()
    hid["doy"] = hid.index.dayofyear
    hid["yr"] = hid.index.year
    pivot = hid.pivot_table(index="yr", columns="doy", values="hi_c")
    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns, y=pivot.index,
        colorscale="YlOrRd", colorbar=dict(title="HI °C"),
    ))
    fig.update_layout(xaxis_title="Day of year", yaxis_title="Year")
    fig = theme.style_fig(fig, height=380)
    fig.update_layout(hovermode="closest")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)")
    return fig


def _counter_fig():
    hid = data.heat_index_daily()
    counts = (hid["hi_c"] > DANGER_C).groupby(hid.index.year).sum()
    fig = go.Figure(go.Bar(x=counts.index, y=counts.to_numpy(), marker_color=theme.RED))
    fig.update_layout(yaxis_title="Days")
    return theme.style_fig(fig, height=380)


def layout(**_):
    hid = data.heat_index_daily()
    if hid.empty:
        return html.Div(theme.card(
            "Database not found. Build it first:  python -m src.data.ingest", title="No data"))
    y_min, y_max = int(hid.index.year.min()), int(hid.index.year.max())
    return html.Div([
        theme.eyebrow("Climate insights · Heat index"),
        html.H1("The climate record", className="h1"),
        html.P(f"Daily heat index from daily max temperature and mean relative humidity, "
               f"{y_min}–{y_max}.", className="lead"),
        _kpis(hid),

        theme.section_head("Multi-year trend"),
        theme.card(
            dcc.Graph(figure=_trend_fig(), config=theme.CHART_CONFIG),
            html.Div([html.Span("PAGASA bands", className="ttl"), *_band_legend()],
                     className="chart-legend"),
            html.P("Shaded bands are PAGASA's heat-index danger categories. Pairing daily max "
                   "temperature with daily mean relative humidity tends to overestimate the heat "
                   "index, since humidity is lowest at peak heat.", className="muted"),
            title="Annual mean heat index",
            subtitle="With PAGASA danger bands",
        ),

        theme.section_head("Across the calendar"),
        html.Div(className="grid-2", children=[
            theme.card(dcc.Graph(figure=_heatmap_fig(), config=theme.CHART_CONFIG),
                       title="Calendar heatmap", subtitle="Daily heat index by day of year & year"),
            theme.card(dcc.Graph(figure=_counter_fig(), config=theme.CHART_CONFIG),
                       title="Dangerous days per year",
                       subtitle=f"Days with heat index above {DANGER_C:.0f} °C"),
        ]),

        theme.section_head("Short-term forecast"),
        theme.card(
            html.Div(className="fc-head", children=[
                html.Div([
                    html.Div("Seasonal projection", className="card-title"),
                    html.Div("Simulated LSTM trajectory of the daily heat index", className="card-sub"),
                ]),
                html.Div(className="fc-right", children=[
                    html.Div(id="ci-fc-metrics"),
                    dcc.RadioItems(id="ci-horizon",
                                   options=[{"label": "7 days", "value": 7},
                                            {"label": "14 days", "value": 14}],
                                   value=14, className="seg"),
                ]),
            ]),
            dcc.Loading(dcc.Graph(id="ci-forecast", config=theme.CHART_CONFIG)),
            html.P("One Monte-Carlo trajectory from the LSTM — the recursive projection with "
                   "residual variability resampled at each step; the shaded band is the 5–95% range "
                   "across simulations. A statistical estimate, not a meteorological forecast; it "
                   "also inherits the Tmax + mean-RH overestimation. Backtest MAE/RMSE measure the "
                   "deterministic mean forecast.", className="muted"),
        ),
    ])


def _forecast_fig(recent, fc, horizon):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(fc["ds"]) + list(fc["ds"][::-1]),
        y=list(fc["yhat_upper"]) + list(fc["yhat_lower"][::-1]),
        fill="toself", fillcolor="rgba(138,21,56,0.13)", line=dict(width=0),
        name="Uncertainty", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=recent.index, y=recent.to_numpy(), name="Actual",
                             mode="lines", line=dict(color=theme.INK, shape="spline", smoothing=0.5)))
    fig.add_trace(go.Scatter(x=fc["ds"], y=fc["yhat"], name="Forecast",
                             mode="lines", line=dict(color=theme.MAROON, dash="dash",
                                                     shape="spline", smoothing=0.5)))
    fig.update_layout(yaxis_title="Heat index (°C)")
    return theme.style_fig(fig, height=360)


def _forecast_metrics(metrics):
    return html.Div(className="fc-metrics", children=[
        html.Div(className="fc-metric", children=[
            html.Span(f"{metrics['mae']:.2f} ", className="v"), html.Span("°C MAE", className="u")]),
        html.Div(className="fc-metric", children=[
            html.Span(f"{metrics['rmse']:.2f} ", className="v"), html.Span("°C RMSE", className="u")]),
    ])


@callback(Output("ci-forecast", "figure"), Output("ci-fc-metrics", "children"),
          Input("ci-horizon", "value"))
def update_forecast(horizon):
    h = int(horizon)
    recent = data.heat_index_daily()["hi_c"].tail(60)
    fc, metrics = data.heat_index_forecast(h)
    return _forecast_fig(recent, fc, h), _forecast_metrics(metrics)


def _band_legend():
    """Color key for the PAGASA danger bands."""
    items = []
    for lo, hi, label in heat_index.PAGASA_BANDS:
        if label == "Not hazardous":
            continue
        rng = f"≥{lo:.0f} °C" if hi == float("inf") else f"{lo:.0f}–{hi:.0f} °C"
        items.append(html.Span(
            [html.Span(className="swatch", style={"background": theme.BAND_COLORS.get(label, "#94a3b8")}),
             f"{label} ({rng})"],
            className="legend-item"))
    return items
