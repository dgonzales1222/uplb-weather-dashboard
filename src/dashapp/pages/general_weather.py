"""General Weather page (Dash) — the "Editorial" UPLB design.

Hero feels-like heat index with a PAGASA danger gauge, latest readings, an
interactive time-series (year + resolution + parameters via a callback), and
monthly/annual climatology. All data/figure logic is reused; only the markup and
styling follow the design.
"""
import calendar

import dash
import numpy as np
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
    "relative_humidity": theme.GREEN, "wind_speed": theme.ORANGE,
    "station_pressure": theme.PURPLE, "wet_bulb_temp": theme.TEAL,
}
AGG = {
    "max_temp": "max", "min_temp": "min", "mean_temp": "mean",
    "wet_bulb_temp": "mean", "relative_humidity": "mean",
    "precipitation": "sum", "wind_speed": "mean",
    "wind_direction": "mean", "station_pressure": "mean",
}

CAPTIONS = {
    "Extreme Danger": "Heatstroke is highly likely. Avoid all outdoor exertion and "
                      "check on vulnerable neighbours.",
    "Danger": "Heat cramps and heat exhaustion are likely; heatstroke is possible with "
              "prolonged exposure. Limit strenuous activity.",
    "Extreme Caution": "Heat cramps and heat exhaustion are possible. Take frequent "
                       "breaks and stay hydrated.",
    "Caution": "Fatigue is possible with prolonged exposure and activity.",
    "Not hazardous": "Conditions are comfortable. No heat-stress precautions needed.",
}


def _u(name: str) -> str:
    u = data.units().get(name, "")
    return f" ({u})" if u else ""


def _resample(frame, resolution):
    if resolution == "Daily":
        return frame
    rule = "MS" if resolution == "Monthly" else "YS"
    return frame.resample(rule).agg(AGG)


def _build_chart(view, label, cols, kind, resolution, year):
    fig = go.Figure()
    if kind == "temp":
        for col, nm, clr in zip(cols, ["Max", "Mean", "Min"], [theme.RED, theme.GOLD, theme.BLUE]):
            fig.add_trace(go.Scatter(x=view.index, y=view[col], name=nm, mode="lines",
                                     line=dict(color=clr, shape="spline", smoothing=0.5)))
        fig.update_layout(xaxis_rangeslider_visible=(resolution == "Daily" and year == "All years"))
    elif kind == "bar":
        fig.add_trace(go.Bar(x=view.index, y=view[cols[0]], marker_color=theme.BLUE))
    else:
        fig.add_trace(go.Scatter(x=view.index, y=view[cols[0]], mode="lines",
                                 line=dict(color=LINE_COLORS.get(cols[0], theme.BLUE),
                                           shape="spline", smoothing=0.5)))
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
    return html.Div(className="controls", children=[
        html.Div(className="ctl", children=[
            html.Label("Year", className="ctl-label"),
            dcc.Dropdown(id="gw-year", options=years, value=str(y_max), clearable=False),
        ]),
        html.Div(className="ctl", children=[
            html.Label("Resolution", className="ctl-label"),
            dcc.RadioItems(id="gw-resolution", options=["Daily", "Monthly", "Yearly"],
                           value="Daily", className="seg"),
        ]),
        html.Div(className="ctl", children=[
            html.Label("Parameters", className="ctl-label"),
            dcc.Checklist(id="gw-parameters", options=[p[0] for p in PARAMETERS],
                          value=[p[0] for p in PARAMETERS], className="pills"),
        ]),
    ])


def _delta(latest, prev, name, dec):
    d = float(latest[name] - prev[name])
    direction = "up" if d > 0.05 else "down" if d < -0.05 else "flat"
    return f"{abs(d):.{dec}f}", direction


def _hero(daily, hid):
    latest, prev = daily.iloc[-1], daily.iloc[-2]
    hi_c = heat_index.heat_index_c(latest["max_temp"], latest["relative_humidity"])
    band = heat_index.classify(hi_c)

    # Decadal warming rate of the annual-mean heat index (the "bigger picture").
    annual = hid.groupby(hid.index.year)["hi_c"].mean()
    slope = np.polyfit(annual.index.to_numpy(), annual.to_numpy(), 1)[0]
    rate = slope * 10.0

    st = data.station()
    lat, lon = st.get("latitude", 14.17), st.get("longitude", 121.24)
    y_min, y_max = int(daily.index.year.min()), int(daily.index.year.max())
    elev = st.get("elevation")
    elev_txt = f"{elev:.0f} m" if elev is not None else "—"

    main = html.Div(className="card2 hero-main", children=[
        html.Div(className="hero-top", children=[
            html.Div([
                html.Div("Feels-like heat index · Daily max", className="feels-label"),
                html.Div(className="feels-row", children=[
                    html.Span(f"{hi_c:.1f}", className="feels-value"),
                    html.Span("°C", className="feels-unit"),
                    theme.band_badge(band),
                ]),
            ]),
            theme.weather_icon(float(latest["precipitation"]), float(latest["relative_humidity"])),
        ]),
        html.Div(className="gauge-block", children=[
            theme.gauge(hi_c),
            html.P(CAPTIONS.get(band, ""), className="gauge-caption"),
        ]),
    ])

    side = html.Div(className="hero-side", children=[
        html.Div(className="card2 bigpic", children=[
            html.Div("The bigger picture", className="bigpic-label"),
            html.Div(className="bigpic-text", children=[
                "Mean heat index is rising ",
                html.Span(f"{rate:+.2f}°C", className="accent"),
                " per decade.",
            ]),
            dcc.Link("See the climate record →", href="/climate-insights", className="bigpic-link"),
        ]),
        html.Div(className="card2", children=[
            html.Div(className="meta-grid", children=[
                _meta("Station", "UPLB-NAS"),
                _meta("Elevation", elev_txt),
                _meta("Record", f"{y_min}–{y_max}"),
                _meta("Source", st.get("source", "ERA5")),
            ]),
        ]),
    ])

    eyebrow = theme.eyebrow(f"LOS BAÑOS, LAGUNA · {lat:.2f}°N, {lon:.2f}°E")
    date_txt = daily.index[-1].strftime("%B %d, %Y").replace(" 0", " ")
    return html.Div([
        eyebrow,
        html.H1("Today at the station", className="h1"),
        html.P(f"Latest observation — {date_txt}. Open-Meteo ERA5 stand-in for the "
               f"UPLB-NAS record.", className="lead"),
        html.Div([main, side], className="hero-grid"),
    ])


def _meta(label, value):
    return html.Div([
        html.Div(label, className="meta-label"),
        html.Div(value, className="meta-value"),
    ])


def _latest_readings(daily):
    latest, prev = daily.iloc[-1], daily.iloc[-2]
    tiles = [
        ("Max temp", f"{latest['max_temp']:.1f}", "°C", _delta(latest, prev, "max_temp", 1)),
        ("Mean temp", f"{latest['mean_temp']:.1f}", "°C", _delta(latest, prev, "mean_temp", 1)),
        ("Min temp", f"{latest['min_temp']:.1f}", "°C", _delta(latest, prev, "min_temp", 1)),
        ("Humidity", f"{latest['relative_humidity']:.0f}", "%", _delta(latest, prev, "relative_humidity", 0)),
        ("Rainfall", f"{latest['precipitation']:.1f}", "mm", None),
        ("Wind", f"{latest['wind_speed']:.1f}", "m/s", _delta(latest, prev, "wind_speed", 1)),
        ("Pressure", f"{latest['station_pressure']:.0f}", "hPa", _delta(latest, prev, "station_pressure", 0)),
        ("Wet bulb", f"{latest['wet_bulb_temp']:.1f}", "°C", _delta(latest, prev, "wet_bulb_temp", 1)),
    ]
    cards = []
    for label, value, unit, delta in tiles:
        if delta is None:
            cards.append(theme.metric_card(label, value, unit))
        else:
            text, direction = delta
            cards.append(theme.metric_card(label, value, unit, text, direction))
    return html.Div([
        theme.section_head("Latest readings"),
        html.Div(cards, className="metric-row"),
    ])


def _climograph(x, rain, temp, rain_title, temp_title):
    """Rainfall bars (left axis) + a smooth temperature spline (right axis)."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=x, y=rain, name="Rainfall", marker_color=theme.BLUE, opacity=0.85),
                  secondary_y=False)
    fig.add_trace(go.Scatter(x=x, y=temp, name="Temperature", mode="lines+markers",
                             line=dict(color=theme.MAROON, width=3, shape="spline", smoothing=1.0),
                             marker=dict(size=6)), secondary_y=True)
    fig.update_layout(bargap=0.3)
    fig.update_yaxes(title_text=rain_title, secondary_y=False, rangemode="tozero",
                     title_font=dict(color=theme.BLUE), tickfont=dict(color=theme.BLUE))
    tmin, tmax = float(min(temp)), float(max(temp))
    pad = max(1.0, (tmax - tmin) * 0.35)
    fig.update_yaxes(title_text=temp_title, secondary_y=True, range=[tmin - pad, tmax + pad],
                     showgrid=False, title_font=dict(color=theme.MAROON), tickfont=dict(color=theme.MAROON))
    return theme.style_fig(fig, height=340)


def _climatology(daily):
    y_min, y_max = int(daily.index.year.min()), int(daily.index.year.max())

    monthly = daily.groupby(daily.index.month).agg(
        mean_temp=("mean_temp", "mean"), precipitation=("precipitation", "mean"))
    months = [calendar.month_abbr[m] for m in monthly.index]
    mf = _climograph(months, monthly["precipitation"], monthly["mean_temp"],
                     f"Mean rain{_u('precipitation')}", f"Mean temp{_u('mean_temp')}")

    annual = daily.groupby(daily.index.year).agg(
        mean_temp=("mean_temp", "mean"), precipitation=("precipitation", "sum"))
    af = _climograph(annual.index, annual["precipitation"], annual["mean_temp"],
                     f"Total rain{_u('precipitation')}", f"Mean temp{_u('mean_temp')}")

    return html.Div([
        theme.section_head("Climatology"),
        html.P(f"Long-term normals over the full record ({y_min}–{y_max}).", className="muted"),
        html.Div(className="grid-2", children=[
            theme.card(dcc.Graph(figure=mf, config=theme.CHART_CONFIG), title="Monthly normals"),
            theme.card(dcc.Graph(figure=af, config=theme.CHART_CONFIG), title="Annual summary"),
        ]),
    ])


def layout(**_):
    daily = data.daily()
    if daily.empty:
        return html.Div(theme.card(
            "Database not found. Build it first:  python -m src.data.ingest",
            title="No data"))
    hid = data.heat_index_daily()
    y_min, y_max = int(daily.index.year.min()), int(daily.index.year.max())
    return html.Div([
        _hero(daily, hid),
        _latest_readings(daily),
        theme.section_head("Explore the record"),
        theme.card(
            _controls(y_min, y_max),
            html.Div(id="gw-ts-heading", className="ts-caption"),
            html.Div(id="gw-timeseries", className="stack"),
        ),
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
