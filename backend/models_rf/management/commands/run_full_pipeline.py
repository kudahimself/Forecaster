"""End-to-end pipeline: rf_run -> portfolio_backtest -> permutation_test.

Glues the three existing commands so `make demo` is a single target, and so
researchers can fire off a full "experiment + significance test" from one
CLI invocation."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from models_rf.runner import run_rf
from permutation.runner import run_permutation_test
from portfolio.runner import backtest_run


class Command(BaseCommand):
    help = "Run RF + backtest + permutation test in sequence."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--experiment", default="rf_crosssectional_us")
        parser.add_argument("--top-k", type=int, default=15)
        parser.add_argument("--top-k-short", type=int, default=0)
        parser.add_argument("--window-months", type=int, default=12)
        parser.add_argument("--min-train-rows", type=int, default=150)
        parser.add_argument("--max-per-sector", type=int, default=None)
        parser.add_argument("--model", default="randomforest")
        parser.add_argument("--seed", type=int, default=0)
        parser.add_argument("--n-permutations", type=int, default=100)
        parser.add_argument("--name", default="")
        parser.add_argument("--tag", action="append", dest="tags", default=[])
        parser.add_argument(
            "--skip-permutations",
            action="store_true",
            help="Run RF + backtest only (fast path for iteration).",
        )
        parser.add_argument("--entry-delay-bdays", type=int, default=1)
        parser.add_argument("--holding", default="next_month")

    def handle(self, *args, **opts) -> None:
        n_perms = opts["n_permutations"]
        total_steps = 2 if opts["skip_permutations"] else 3

        self.stdout.write(self.style.NOTICE(f"[1/{total_steps}] rf_run..."))
        run_id = run_rf(
            experiment=opts["experiment"],
            top_k=opts["top_k"],
            top_k_short=opts["top_k_short"],
            window_months=opts["window_months"],
            min_train_rows=opts["min_train_rows"],
            model_type=opts["model"],
            seed=opts["seed"],
            max_per_sector=opts["max_per_sector"],
            tags=opts["tags"] or None,
            name=opts["name"],
        )
        self.stdout.write(self.style.SUCCESS(f"    run_id = {run_id}"))

        self.stdout.write(self.style.NOTICE(f"[2/{total_steps}] portfolio_backtest..."))
        summary = backtest_run(
            run_id,
            entry_delay_bdays=opts["entry_delay_bdays"],
            holding=opts["holding"],
        )
        cum = summary.get("cum_return")
        sharpe = summary.get("ann_sharpe")
        self.stdout.write(
            self.style.SUCCESS(
                f"    cum_return={cum} ann_sharpe={sharpe} "
                f"n_days={summary.get('n_days')}"
            )
        )

        if opts["skip_permutations"]:
            self.stdout.write(
                self.style.SUCCESS(f"\nDone (no permutations). run_id={run_id}")
            )
            return

        self.stdout.write(
            self.style.NOTICE(
                f"[3/{total_steps}] permutation_test (N={n_perms}, "
                "may take a while on the full universe)..."
            )
        )
        perm = run_permutation_test(run_id, n_permutations=n_perms)
        self.stdout.write(
            self.style.SUCCESS(
                f"    baseline={perm['baseline_metric']:.5f} "
                f"median_perm={perm['median_perm']} "
                f"p_two_sided={perm['p_two_sided']} "
                f"n={perm['n_valid']}/{perm['n_permutations']}"
            )
        )

        self.stdout.write(self.style.SUCCESS(f"\nDone. run_id={run_id}"))
