from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

UNIVERSE_DIR = Path(__file__).resolve().parent / "config"


@lru_cache(maxsize=1)
def load_sectors(filename: str = "sectors.yml") -> dict[str, str]:
    """Load the sector mapping. Returns {ticker: sector_name}.

    Source file is sector -> [tickers], flattened here to ticker -> sector."""
    path = UNIVERSE_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Sector config not found: {path}")
    with path.open() as fh:
        data = yaml.safe_load(fh)
    out: dict[str, str] = {}
    for sector, tickers in (data.get("sectors") or {}).items():
        for t in tickers or []:
            out[t] = sector
    return out


@lru_cache(maxsize=16)
def load_universe(name: str = "default") -> dict:
    """Load a universe YAML. `default` maps to `top100_liquid_us.yml` if present,
    otherwise to the single universe.yml in this directory."""
    candidate = UNIVERSE_DIR / f"{name}.yml"
    if not candidate.exists() and name == "default":
        candidate = UNIVERSE_DIR / "universe.yml"
    if not candidate.exists():
        raise FileNotFoundError(f"Universe config not found: {candidate}")
    with candidate.open() as fh:
        data = yaml.safe_load(fh)
    if "tickers" not in data or not isinstance(data["tickers"], list):
        raise ValueError(f"Universe {candidate} missing 'tickers' list")
    # De-dupe while preserving order.
    seen = set()
    tickers = []
    for t in data["tickers"]:
        if t not in seen:
            seen.add(t)
            tickers.append(t)
    data["tickers"] = tickers
    return data
