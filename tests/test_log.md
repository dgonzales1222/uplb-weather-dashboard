### Test result for clean and ingest (17 June 2026)
```python
================================================ test session starts =================================================
platform darwin -- Python 3.13.9, pytest-9.1.0, pluggy-1.6.0 -- /Users/dgonzales22/Documents/AVCAD Project/uplb-nas-dashboard/venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/dgonzales22/Documents/AVCAD Project/avcad-project-uplb-weather-dashboard
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.14.0
collected 13 items                                                                                                   

tests/test_clean.py::test_daily_from_hourly_means PASSED                                                       [  7%]
tests/test_clean.py::test_build_daily_columns_and_merge PASSED                                                 [ 15%]
tests/test_clean.py::test_validate_passes_clean_frame PASSED                                                   [ 23%]
tests/test_clean.py::test_validate_allows_nan_values PASSED                                                    [ 30%]
tests/test_clean.py::test_validate_rejects_rh_out_of_range PASSED                                              [ 38%]
tests/test_clean.py::test_validate_rejects_negative_precip PASSED                                              [ 46%]
tests/test_clean.py::test_validate_rejects_max_below_min PASSED                                                [ 53%]
tests/test_clean.py::test_validate_rejects_duplicate_dates PASSED                                              [ 61%]
tests/test_clean.py::test_validate_rejects_missing_calendar_date PASSED                                        [ 69%]
tests/test_ingest.py::test_to_long_shape_and_mapping PASSED                                                    [ 76%]
tests/test_ingest.py::test_to_long_maps_nan_to_none PASSED                                                     [ 84%]
tests/test_ingest.py::test_build_db_end_to_end PASSED                                                          [ 92%]
tests/test_ingest.py::test_build_db_is_idempotent PASSED                                                       [100%]
```

### Test result for clean and ingest, and heat index (18 June 2026)
```
================================================ test session starts =================================================
platform darwin -- Python 3.13.9, pytest-9.1.0, pluggy-1.6.0 -- /Users/dgonzales22/Documents/AVCAD Project/uplb-nas-dashboard/venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/dgonzales22/Documents/AVCAD Project/avcad-project-uplb-weather-dashboard
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.14.0
collected 31 items                                                                                                   

tests/test_clean.py::test_daily_from_hourly_means PASSED                                                       [  3%]
tests/test_clean.py::test_build_daily_columns_and_merge PASSED                                                 [  6%]
tests/test_clean.py::test_validate_passes_clean_frame PASSED                                                   [  9%]
tests/test_clean.py::test_validate_allows_nan_values PASSED                                                    [ 12%]
tests/test_clean.py::test_validate_rejects_rh_out_of_range PASSED                                              [ 16%]
tests/test_clean.py::test_validate_rejects_negative_precip PASSED                                              [ 19%]
tests/test_clean.py::test_validate_rejects_max_below_min PASSED                                                [ 22%]
tests/test_clean.py::test_validate_rejects_duplicate_dates PASSED                                              [ 25%]
tests/test_clean.py::test_validate_rejects_missing_calendar_date PASSED                                        [ 29%]
tests/test_heat_index.py::test_reference_points_match_nws PASSED                                               [ 32%]
tests/test_heat_index.py::test_simple_form_in_cool_regime PASSED                                               [ 35%]
tests/test_heat_index.py::test_low_humidity_adjustment PASSED                                                  [ 38%]
tests/test_heat_index.py::test_high_humidity_adjustment PASSED                                                 [ 41%]
tests/test_heat_index.py::test_celsius_wrapper_matches_fahrenheit PASSED                                       [ 45%]
tests/test_heat_index.py::test_classify_boundaries[26-Not hazardous] PASSED                                    [ 48%]
tests/test_heat_index.py::test_classify_boundaries[27-Caution] PASSED                                          [ 51%]
tests/test_heat_index.py::test_classify_boundaries[32-Caution] PASSED                                          [ 54%]
tests/test_heat_index.py::test_classify_boundaries[33-Extreme Caution] PASSED                                  [ 58%]
tests/test_heat_index.py::test_classify_boundaries[41-Extreme Caution] PASSED                                  [ 61%]
tests/test_heat_index.py::test_classify_boundaries[42-Danger] PASSED                                           [ 64%]
tests/test_heat_index.py::test_classify_boundaries[51-Danger] PASSED                                           [ 67%]
tests/test_heat_index.py::test_classify_boundaries[52-Extreme Danger] PASSED                                   [ 70%]
tests/test_heat_index.py::test_classify_boundaries[60-Extreme Danger] PASSED                                   [ 74%]
tests/test_heat_index.py::test_classify_nan_is_none PASSED                                                     [ 77%]
tests/test_heat_index.py::test_heat_index_f_vectorized_over_series PASSED                                      [ 80%]
tests/test_heat_index.py::test_classify_vectorized PASSED                                                      [ 83%]
tests/test_heat_index.py::test_scalar_input_returns_float PASSED                                               [ 87%]
tests/test_ingest.py::test_to_long_shape_and_mapping PASSED                                                    [ 90%]
tests/test_ingest.py::test_to_long_maps_nan_to_none PASSED                                                     [ 93%]
tests/test_ingest.py::test_build_db_end_to_end PASSED                                                          [ 96%]
tests/test_ingest.py::test_build_db_is_idempotent PASSED                                                       [100%]

================================================= 31 passed in 0.64s =================================================
```