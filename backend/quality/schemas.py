"""Pandera schemas for raw tables. Used by the schema_* checks in quality.checks."""

from __future__ import annotations

import pandera.pandas as pa
from pandera.pandas import Check, Column, DataFrameSchema

raw_prices_schema = DataFrameSchema(
    {
        "symbol": Column(str, nullable=False),
        "date": Column("datetime64[ns]", nullable=False),
        "open": Column(float, nullable=True, checks=Check.ge(0)),
        "high": Column(float, nullable=True, checks=Check.ge(0)),
        "low": Column(float, nullable=True, checks=Check.ge(0)),
        "close": Column(float, nullable=True, checks=Check.ge(0)),
        "adj_close": Column(float, nullable=True, checks=Check.ge(0)),
        "volume": Column(
            "Int64", nullable=True, checks=Check.ge(0)
        ),  # pandas nullable int
    },
    strict=False,
    coerce=True,
)

raw_factors_schema = DataFrameSchema(
    {
        "date": Column("datetime64[ns]", nullable=False),
        "mkt_rf": Column(float, nullable=True, checks=Check.in_range(-0.5, 0.5)),
        "smb": Column(float, nullable=True, checks=Check.in_range(-0.5, 0.5)),
        "hml": Column(float, nullable=True, checks=Check.in_range(-0.5, 0.5)),
        "rmw": Column(float, nullable=True, checks=Check.in_range(-0.5, 0.5)),
        "cma": Column(float, nullable=True, checks=Check.in_range(-0.5, 0.5)),
        "mom": Column(float, nullable=True, checks=Check.in_range(-0.5, 0.5)),
        "rf": Column(float, nullable=True, checks=Check.in_range(-0.1, 0.1)),
    },
    strict=False,
    coerce=True,
)
