"""General Weather page (Dash) — parity with the former Streamlit Home page.

Latest readings with a feels-like heat index, interactive time-series (year +
resolution + parameters via a callback), and monthly/annual climatology.
"""
import calendar

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html
from plotly.subplots import make_subplots

from src.dashapp import data, theme
from src.features import heat_index

dash.register_page(__name__, path="/", name="General Weather", order=0)

# Chartable parameter groups: (label, columns, kind).
PARAMETERS = [
    ("Temperature", ["max_temp", "mean_temp", "min_temp"], "temp"),
    ("Rainfall", ["precipitation"], "bar"),
    ("Relative humidity", ["relative_humidity"], "line"),
    ("Wind speed", ["wind_speed"], "line"),
    ("Station pressure", ["station_pressure"], "line"),
    ("Wet-bulb temperature", ["wet_bulb_temp"], "line"),
]
LINE_COLORS = {
    "relative_humidity": "#10b981", "wind_speed": "#f59e0b",
    "station_pressure": "#8b5cf6", "wet_bulb_temp": "#06b6d4",
}
AGG = {
    "max_temp": "max", "min_temp": "min", "mean_temp": "mean",
    "wet_bulb_temp": "mean", "relative_humidity": "mean",
    "precipitation": "sum", "wind_speed": "mean",
    "wind_direction": "mean", "station_pressure": "mean",
}


def _u(name: str) -> str:
    return f" ({data.units().get(name, '')})" if data.units().get(name) else ""


def _resample(frame, resolution):
    if resolution == "Daily":
        return frame
    rule = "MS" if resolution == "Monthly" else "YS"
    return frame.resample(rule).agg(AGG)


def _build_chart(view, label, cols, kind, resolution, year):
    fig = go.Figure()
    if kind == "temp":
        for col, nm, clr in zip(cols, ["Max", "Mean", "Min"], ["#ef4444", "#f59e0b", "#3b82f6"]):
            fig.add_trace(go.Scatter(x=view.index, y=view[col], name=nm, mode="lines", line_color=clr))
        fig.update_layout(xaxis_rangeslider_visible=(resolution == "Daily" and year == "All years"))
    elif kind == "bar":
        fig.add_trace(go.Bar(x=view.index, y=view[cols[0]], marker_color="#3b82f6"))
    else:
        fig.add_trace(go.Scatter(x=view.index, y=view[cols[0]], mode="lines",
                                 line_color=LINE_COLORS.get(cols[0], "#3b82f6")))
    fig.update_layout(title=label, yaxis_title=_u(cols[0]).strip(" ()"))
    return theme.style_fig(fig)


def _timeseries(year, resolution, parameters):
    """Return (list of dcc.Graph, heading text) for the current controls."""
    daily = data.daily()
    if year == "All years":
        ts = daily
        span = f"{daily.index.year.min()}–{daily.index.year.max()}"
    else:
        ts = daily[daily.index.year == int(year)]
        span = year
    view = _resample(ts, resolution)

    chosen = [p for p in PARAMETERS if p[0] in (parameters or [])]
    if not chosen:
        return [html.Div("Select at least one parameter.", className="muted")], "Time series"
    graphs = [
        dcc.Graph(figure=_build_chart(view, label, cols, kind, resolution, year),
                  config=theme.CHART_CONFIG)
        for label, cols, kind in chosen
    ]
    return graphs, f"Time series — {span} · {resolution.lower()}"


def _controls(y_min, y_max):
    years = ["All years"] + [str(y) for y in range(y_max, y_min - 1, -1)]
    return dbc.Card(dbc.CardBody([
        html.Div("Controls", className="sidebar-title"),
        dbc.Row([
            dbc.Col([
                html.Label("Year", className="metric-label"),
                dcc.Dropdown(id="gw-year", options=years, value="All years", clearable=False),
            ], md=3, sm=6),
            dbc.Col([
                html.Label("Resolution", className="metric-label d-block"),
                dcc.RadioItems(id="gw-resolution", options=["Daily", "Monthly", "Yearly"],
                               value="Daily", inline=True,
                               inputClassName="me-1", labelClassName="me-3"),
            ], md="auto"),
        ], className="g-3 align-items-end"),
        html.Label("Parameters", className="metric-label d-block mt-3"),
        dcc.Checklist(id="gw-parameters", options=[p[0] for p in PARAMETERS],
                      value=[p[0] for p in PARAMETERS], inline=True,
                      inputClassName="me-1", labelClassName="me-4"),
    ]))


def _latest_readings(daily):
    latest, prev = daily.iloc[-1], daily.iloc[-2]

    def d(n):
        return f"{latest[n] - prev[n]:+.1f}"

    hi_c = heat_index.heat_index_c(latest["max_temp"], latest["relative_humidity"])
    band = heat_index.classify(hi_c)
    feels = html.Div(className="feels", children=[
        "🌡️ Heat index (feels-like, daily max): ", html.B(f"{hi_c:.1f} °C "), theme.band_badge(band),
    ])

    tiles = [
        (f"Max temp{_u('max_temp')}", f"{latest['max_temp']:.1f}", d("max_temp")),
        (f"Min temp{_u('min_temp')}", f"{latest['min_temp']:.1f}", d("min_temp")),
        (f"Mean temp{_u('mean_temp')}", f"{latest['mean_temp']:.1f}", d("mean_temp")),
        (f"Humidity{_u('relative_humidity')}", f"{latest['relative_humidity']:.0f}", d("relative_humidity")),
        (f"Rainfall{_u('precipitation')}", f"{latest['precipitation']:.1f}", None),
        (f"Wind speed{_u('wind_speed')}", f"{latest['wind_speed']:.1f}", d("wind_speed")),
        (f"Pressure{_u('station_pressure')}", f"{latest['station_pressure']:.0f}", d("station_pressure")),
        (f"Wet bulb{_u('wet_bulb_temp')}", f"{latest['wet_bulb_temp']:.1f}", d("wet_bulb_temp")),
    ]
    grid = dbc.Row([dbc.Col(theme.metric_card(l, v, dl), md=3, sm=6) for l, v, dl in tiles],
                   className="g-2")
    return dbc.Card(dbc.CardBody([
        html.H5(f"Latest readings — {daily.index[-1].date()}"),
        feels, grid,
    ]))


RAIN_BLUE = "#3b82f6"
TEMP_RED = "#ef4444"


def _climograph(x, rain, temp, title, rain_title, temp_title):
    """Climograph: rainfall bars (left axis) + a smooth temperature spline (right
    axis). Each axis is colored to match its series so the scales are unambiguous.
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=x, y=rain, name="Rainfall", marker_color="#93c5fd",
                         opacity=0.9), secondary_y=False)
    fig.add_trace(go.Scatter(x=x, y=temp, name="Temperature", mode="lines+markers",
                             line=dict(color=TEMP_RED, width=3, shape="spline", smoothing=1.0),
                             marker=dict(size=6)), secondary_y=True)
    fig.update_layout(title=title, bargap=0.3)
    # Left (rain) axis from zero, blue; right (temp) axis padded, red.
    fig.update_yaxes(title_text=rain_title, secondary_y=False, rangemode="tozero",
                     title_font=dict(color=RAIN_BLUE), tickfont=dict(color=RAIN_BLUE))
    tmin, tmax = float(min(temp)), float(max(temp))
    pad = max(1.0, (tmax - tmin) * 0.35)
    fig.update_yaxes(title_text=temp_title, secondary_y=True, range=[tmin - pad, tmax + pad],
                     showgrid=False, title_font=dict(color=TEMP_RED), tickfont=dict(color=TEMP_RED))
    return theme.style_fig(fig, height=360)


def _climatology(daily):
    y_min, y_max = int(daily.index.year.min()), int(daily.index.year.max())

    monthly = daily.groupby(daily.index.month).agg(
        mean_temp=("mean_temp", "mean"), precipitation=("precipitation", "mean"))
    months = [calendar.month_abbr[m] for m in monthly.index]
    mf = _climograph(months, monthly["precipitation"], monthly["mean_temp"],
                     "Monthly normals", f"Mean rain{_u('precipitation')}",
                     f"Mean temp{_u('mean_temp')}")

    annual = daily.groupby(daily.index.year).agg(
        mean_temp=("mean_temp", "mean"), precipitation=("precipitation", "sum"))
    af = _climograph(annual.index, annual["precipitation"], annual["mean_temp"],
                     "Annual summary", f"Total rain{_u('precipitation')}",
                     f"Mean temp{_u('mean_temp')}")

    return dbc.Card(dbc.CardBody([
        html.H5("Climatology"),
        html.Div(f"Long-term normals over the full record ({y_min}–{y_max}).", className="muted"),
        dcc.Graph(figure=mf, config=theme.CHART_CONFIG),
        dcc.Graph(figure=af, config=theme.CHART_CONFIG),
    ]))


def layout(**_):
    daily = data.daily()
    if daily.empty:
        return dbc.Alert("Database not found. Build it first:  python -m src.data.ingest",
                         color="warning")
    y_min, y_max = int(daily.index.year.min()), int(daily.index.year.max())
    return html.Div([
        _controls(y_min, y_max),
        _latest_readings(daily),
        dbc.Card(dbc.CardBody([html.H5(id="gw-ts-heading"), html.Div(id="gw-timeseries")])),
        _climatology(daily),
    ])


@callback(
    Output("gw-timeseries", "children"),
    Output("gw-ts-heading", "children"),
    Input("gw-year", "value"),
    Input("gw-resolution", "value"),
    Input("gw-parameters", "value"),
)
def update_timeseries(year, resolution, parameters):
    return _timeseries(year, resolution, parameters)
