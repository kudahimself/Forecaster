from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("runs/", views.RunListView.as_view(), name="run-list"),
    path("runs/<str:run_id>/", views.RunDetailView.as_view(), name="run-detail"),
    path(
        "runs/<str:run_id>/portfolio-returns/",
        views.run_portfolio_returns,
        name="run-portfolio-returns",
    ),
    path(
        "runs/<str:run_id>/perm-metrics/",
        views.run_perm_metrics,
        name="run-perm-metrics",
    ),
    path("experiments/", views.ExperimentListView.as_view(), name="experiment-list"),
    path(
        "feature-importance/",
        views.feature_importance_aggregation,
        name="feature-importance",
    ),
    path("dq/runs/", views.dq_runs_list, name="dq-runs"),
    path("dq/runs/<str:run_id>/", views.dq_run_detail, name="dq-run-detail"),
    path("ingest/status/", views.ingest_status, name="ingest-status"),
    path("scheduler/runs/", views.scheduler_runs, name="scheduler-runs"),
]
