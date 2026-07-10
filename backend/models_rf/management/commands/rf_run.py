from django.core.management.base import BaseCommand

from models_rf.runner import run_rf


class Command(BaseCommand):
    help = "Run a Random Forest walk-forward strategy and log to the tracker."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--experiment", default="rf_crosssectional_us")
        parser.add_argument("--top-k", type=int, default=15)
        parser.add_argument(
            "--top-k-short",
            type=int,
            default=0,
            help="Number of short picks per rebalance. 0 (default) = long-only.",
        )
        parser.add_argument("--window-months", type=int, default=12)
        parser.add_argument("--min-train-rows", type=int, default=150)
        parser.add_argument("--tune", action="store_true", help="Enable hyperparameter search (slower).")
        parser.add_argument("--model", default="randomforest", choices=["randomforest", "ridge"])
        parser.add_argument("--seed", type=int, default=0)
        parser.add_argument("--universe", default="default")
        parser.add_argument(
            "--max-per-sector",
            type=int,
            default=None,
            help="Max picks per GICS sector (applies per side in long-short). "
                 "Requires `populate_sectors` to have been run. "
                 "Default: unconstrained.",
        )
        parser.add_argument("--tag", action="append", dest="tags", default=[])
        parser.add_argument("--name", default="")

    def handle(self, *args, **opts) -> None:
        run_id = run_rf(
            experiment=opts["experiment"],
            top_k=opts["top_k"],
            top_k_short=opts["top_k_short"],
            window_months=opts["window_months"],
            min_train_rows=opts["min_train_rows"],
            tune_model=opts["tune"],
            model_type=opts["model"],
            seed=opts["seed"],
            universe=opts["universe"],
            max_per_sector=opts["max_per_sector"],
            tags=opts["tags"] or None,
            name=opts["name"],
        )
        self.stdout.write(self.style.SUCCESS(f"run_id={run_id}"))
