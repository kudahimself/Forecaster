from django.core.management.base import BaseCommand, CommandError

from permutation.runner import run_permutation_test


class Command(BaseCommand):
    help = (
        "Run a within-date permutation test against an RF baseline run. "
        "Persists perm_summary row and a parquet artifact of the full metric array."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument("--run-id", required=True)
        parser.add_argument("--n-permutations", type=int, default=100)
        parser.add_argument("--seed-base", type=int, default=42)

    def handle(self, *args, **opts) -> None:
        try:
            summary = run_permutation_test(
                opts["run_id"],
                n_permutations=opts["n_permutations"],
                seed_base=opts["seed_base"],
            )
        except RuntimeError as exc:
            raise CommandError(str(exc))
        self.stdout.write(
            self.style.SUCCESS(
                "perm test summary: baseline={baseline_metric:.6f} "
                "median_perm={median_perm} p_two_sided={p_two_sided} "
                "effect_size={effect_size} n_valid={n_valid}/{n_permutations} "
                "artifact={artifact_path}".format(**summary)
            )
        )
