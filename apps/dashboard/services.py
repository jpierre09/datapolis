from datetime import datetime, timedelta

from django.db.models import Count
from django.db.models.functions import TruncWeek
from django.utils import timezone

from apps.data_sources.models import DataSource
from apps.data_visualizations.models import ProjectVisualization
from apps.portfolio_projects.models import PortfolioProject


def build_overview_activity(owner, weeks=12, recent_limit=6):
    if owner is None:
        return {
            "activity_weeks": [],
            "recent_activity_events": [],
            "has_activity": False,
        }

    current_week_start = _get_current_week_start()
    first_week_start = current_week_start - timedelta(weeks=weeks - 1)
    start_datetime = timezone.make_aware(datetime.combine(first_week_start, datetime.min.time()))

    activity_weeks = _build_weekly_activity(owner, first_week_start, start_datetime, weeks)
    recent_activity_events = _build_recent_activity_events(owner, start_datetime, recent_limit)

    has_activity = any(
        week["proyectos_creados"] or week["datasets_subidos"] or week["visualizaciones_creadas"]
        for week in activity_weeks
    )

    return {
        "activity_weeks": activity_weeks,
        "recent_activity_events": recent_activity_events,
        "has_activity": has_activity,
    }


def _get_current_week_start():
    today = timezone.localdate()
    return today - timedelta(days=today.weekday())


def _build_weekly_activity(owner, first_week_start, start_datetime, weeks):
    weeks_by_start = {}

    for offset in range(weeks):
        week_start = first_week_start + timedelta(weeks=offset)
        weeks_by_start[week_start] = {
            "week_start": week_start.isoformat(),
            "week_label": week_start.strftime("%d/%m"),
            "proyectos_creados": 0,
            "datasets_subidos": 0,
            "visualizaciones_creadas": 0,
        }

    weekly_project_counts = (
        PortfolioProject.objects.filter(owner=owner, created_at__gte=start_datetime)
        .annotate(week=TruncWeek("created_at"))
        .values("week")
        .annotate(total=Count("id"))
    )
    weekly_dataset_counts = (
        DataSource.objects.filter(project__owner=owner, uploaded_at__gte=start_datetime)
        .annotate(week=TruncWeek("uploaded_at"))
        .values("week")
        .annotate(total=Count("id"))
    )
    weekly_visualization_counts = (
        ProjectVisualization.objects.filter(portfolio_project__owner=owner, created_at__gte=start_datetime)
        .annotate(week=TruncWeek("created_at"))
        .values("week")
        .annotate(total=Count("id"))
    )

    _merge_weekly_counts(weeks_by_start, weekly_project_counts, "proyectos_creados")
    _merge_weekly_counts(weeks_by_start, weekly_dataset_counts, "datasets_subidos")
    _merge_weekly_counts(weeks_by_start, weekly_visualization_counts, "visualizaciones_creadas")

    return list(weeks_by_start.values())


def _merge_weekly_counts(weeks_by_start, weekly_counts, target_key):
    for row in weekly_counts:
        week_value = row.get("week")
        if week_value is None:
            continue

        week_start = _normalize_week_start(week_value)
        if week_start in weeks_by_start:
            weeks_by_start[week_start][target_key] = row.get("total", 0)


def _normalize_week_start(week_value):
    if hasattr(week_value, "date"):
        return week_value.date()

    return week_value


def _build_recent_activity_events(owner, start_datetime, recent_limit):
    events = []

    for project in (
        PortfolioProject.objects.filter(owner=owner, created_at__gte=start_datetime)
        .order_by("-created_at")
        .values("id", "title", "slug", "created_at")
    ):
        events.append(
            {
                "kind": "project",
                "badge": "Proyecto",
                "title": project["title"],
                "text": "Proyecto creado en el portafolio.",
                "date_label": _format_activity_date(project["created_at"]),
                "timestamp": project["created_at"],
            }
        )

    for data_source in (
        DataSource.objects.filter(project__owner=owner, uploaded_at__gte=start_datetime)
        .select_related("project")
        .order_by("-uploaded_at")
        .values("id", "name", "uploaded_at", "project__title")
    ):
        events.append(
            {
                "kind": "dataset",
                "badge": "Dataset",
                "title": data_source["name"],
                "text": f'Subido al proyecto "{data_source["project__title"]}".',
                "date_label": _format_activity_date(data_source["uploaded_at"]),
                "timestamp": data_source["uploaded_at"],
            }
        )

    for visualization in (
        ProjectVisualization.objects.filter(portfolio_project__owner=owner, created_at__gte=start_datetime)
        .select_related("portfolio_project")
        .order_by("-created_at")
        .values("id", "title", "created_at", "portfolio_project__title")
    ):
        events.append(
            {
                "kind": "visualization",
                "badge": "Visualización",
                "title": visualization["title"],
                "text": f'Se creó para el proyecto "{visualization["portfolio_project__title"]}".',
                "date_label": _format_activity_date(visualization["created_at"]),
                "timestamp": visualization["created_at"],
            }
        )

    events.sort(key=lambda event: event["timestamp"], reverse=True)

    for event in events:
        event.pop("timestamp", None)

    return events[:recent_limit]


def _format_activity_date(value):
    local_value = timezone.localtime(value)
    return local_value.strftime("%d/%m/%Y")
