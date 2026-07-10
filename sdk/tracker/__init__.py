"""Notebook-facing SDK for the Forecaster research warehouse.

Typical usage from a Jupyter cell:

    import tracker

    with tracker.run(
        experiment="rf_crosssectional_us",
        params={"top_k": 15, "window_months": 12, "seed": 0},
        tags=["baseline"],
    ) as r:
        # ... training code ...
        r.log_metric("oos_sharpe", 1.2)
        r.log_metric("oos_mae", 0.021)
        r.log_importance({"rsi": 0.12, "macd": 0.08, "return_12m": 0.18})
        r.log_artifact("equity_curve", "/path/to/plot.png", kind="plot")

The SDK writes directly to the SQLite warehouse at `<repo>/data/warehouse.db`
using only the stdlib `sqlite3` module — no Django or ORM dependency.
"""

from tracker.client import Run, attach, run
from tracker.db import resolve_warehouse_path

__all__ = ["Run", "run", "attach", "resolve_warehouse_path"]
