"""Heat-index unit tests — Phase 3.

Validates the NWS heat-index math (src/features/heat_index.py) against published
NWS reference values and exercises the PAGASA classification + vectorization.
Pure tests (no data files). Run with:  pytest
"""
import numpy as np
import pandas as pd
import pytest

from src.features import heat_index as hi


# --- heat_index_f: NWS reference points -------------------------------------

def test_reference_points_match_nws():
    # Rothfusz regression values (also the anchors quoted in the module stub).
    assert hi.heat_index_f(95, 50) == pytest.approx(105.2, abs=0.5)
    assert hi.heat_index_f(90, 70) == pytest.approx(105.9, abs=0.5)
    # A high point straight off the NWS chart — strong check on the coefficients.
    assert hi.heat_index_f(110, 40) == pytest.approx(136, abs=1.0)


def test_simple_form_in_cool_regime():
    # Below ~80 °F the simple Steadman form is used (no Rothfusz blow-up).
    val = hi.heat_index_f(75, 40)
    assert val < 80
    assert val == pytest.approx(74.1, abs=0.5)


def test_low_humidity_adjustment():
    # RH < 13% with 80–112 °F subtracts an adjustment from the regression.
    assert hi.heat_index_f(100, 10) == pytest.approx(94.1, abs=0.5)


def test_high_humidity_adjustment():
    # RH > 85% with 80–87 °F adds an adjustment to the regression.
    assert hi.heat_index_f(85, 90) == pytest.approx(101.8, abs=0.5)


# --- heat_index_c: °C wrapper -----------------------------------------------

def test_celsius_wrapper_matches_fahrenheit():
    # 35 °C == 95 °F; the °C result is just the °F result converted back.
    assert hi.heat_index_c(35, 50) == pytest.approx(hi._f_to_c(hi.heat_index_f(95, 50)))
    assert hi.heat_index_c(35, 50) == pytest.approx(40.7, abs=0.3)


# --- classify: PAGASA bands -------------------------------------------------

@pytest.mark.parametrize("hi_c, label", [
    (26, "Not hazardous"),
    (27, "Caution"),
    (32, "Caution"),
    (33, "Extreme Caution"),
    (41, "Extreme Caution"),
    (42, "Danger"),          # the README's ">41 °C heat index" danger threshold
    (51, "Danger"),
    (52, "Extreme Danger"),
    (60, "Extreme Danger"),
])
def test_classify_boundaries(hi_c, label):
    assert hi.classify(hi_c) == label


def test_classify_nan_is_none():
    assert hi.classify(float("nan")) is None


# --- vectorization ----------------------------------------------------------

def test_heat_index_f_vectorized_over_series():
    out = hi.heat_index_f(pd.Series([95.0, 90.0]), pd.Series([50.0, 70.0]))
    assert np.asarray(out) == pytest.approx([105.2, 105.9], abs=0.5)


def test_classify_vectorized():
    out = hi.classify(np.array([30.0, 45.0, np.nan]))
    assert list(out) == ["Caution", "Danger", None]


def test_scalar_input_returns_float():
    assert isinstance(hi.heat_index_f(95, 50), float)
    assert isinstance(hi.heat_index_c(35, 50), float)
