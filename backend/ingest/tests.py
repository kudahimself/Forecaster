"""Tests for ingest helpers (universe + sectors) and models."""

from django.test import TestCase

from _test_fixtures import seed_raw_data
from ingest.models import RawFactor, RawPrice, Symbol
from ingest.universe import load_sectors, load_universe


class UniverseLoaderTests(TestCase):
    def test_default_universe_loads_without_error(self):
        u = load_universe("default")
        self.assertIn("tickers", u)
        self.assertGreater(len(u["tickers"]), 50)
        self.assertEqual(len(u["tickers"]), len(set(u["tickers"])))

    def test_smoke_universe_has_three_tickers(self):
        u = load_universe("smoke")
        self.assertEqual(u["tickers"], ["AAPL", "MSFT", "NVDA"])


class SectorLoaderTests(TestCase):
    def test_sectors_covers_every_universe_ticker(self):
        universe = load_universe("default")["tickers"]
        sectors = load_sectors()
        missing = [t for t in universe if t not in sectors]
        self.assertEqual(missing, [], f"universe tickers with no sector: {missing}")

    def test_major_tickers_have_correct_sector(self):
        sectors = load_sectors()
        self.assertEqual(sectors["AAPL"], "Information Technology")
        self.assertEqual(sectors["V"], "Financials")
        self.assertEqual(sectors["META"], "Communication Services")
        self.assertEqual(sectors["ADP"], "Industrials")


class RawModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.fixture = seed_raw_data(
            symbols=["XYZ"], start="2024-01-01", end="2024-03-31", seed=1
        )

    def test_raw_prices_populated(self):
        self.assertEqual(RawPrice.objects.count(), self.fixture["n_price_rows"])
        self.assertEqual(RawPrice.objects.values("symbol").distinct().count(), 1)

    def test_raw_factors_populated(self):
        self.assertEqual(RawFactor.objects.count(), self.fixture["n_factor_rows"])

    def test_raw_price_unique_constraint(self):
        from django.db import IntegrityError, transaction

        row = RawPrice.objects.first()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                RawPrice.objects.create(
                    symbol=row.symbol,
                    date=row.date,
                    open=row.open,
                    high=row.high,
                    low=row.low,
                    close=row.close,
                    adj_close=row.adj_close,
                    volume=row.volume,
                    source=row.source,
                )

    def test_symbol_dim_populated(self):
        s = Symbol.objects.get(symbol="XYZ")
        self.assertEqual(s.sector, "Information Technology")
