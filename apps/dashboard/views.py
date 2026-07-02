from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from apps.data_sources.models import DataSource
from apps.data_visualizations.models import ProjectVisualization
from apps.portfolio_projects.models import PortfolioProject, ProjectType

STATUS_LABELS = {
    PortfolioProject.Status.DRAFT: "Borrador",
    PortfolioProject.Status.PUBLISHED: "Publicado",
    PortfolioProject.Status.ARCHIVED: "Archivado",
}
STATUS_FILTERS = {"all", PortfolioProject.Status.DRAFT, PortfolioProject.Status.PUBLISHED, PortfolioProject.Status.ARCHIVED}


def overview(request):
    active_data_sources_prefetch = Prefetch(
        "data_sources",
        queryset=DataSource.objects.filter(is_active=True).order_by("-uploaded_at"),
        to_attr="active_data_sources",
    )
    recent_projects = list(
        PortfolioProject.objects.select_related("project_type", "category")
        .prefetch_related(active_data_sources_prefetch)
        .order_by("-updated_at")[:6]
    )

    for project in recent_projects:
        project.status_label = STATUS_LABELS.get(project.status, project.status)
        main_dataset = project.active_data_sources[0] if project.active_data_sources else None
        project.main_dataset_name = main_dataset.name if main_dataset else "Sin dataset"

    metrics = {
        "total_projects": PortfolioProject.objects.count(),
        "published_projects": PortfolioProject.objects.filter(status=PortfolioProject.Status.PUBLISHED).count(),
        "draft_projects": PortfolioProject.objects.filter(status=PortfolioProject.Status.DRAFT).count(),
        "datasets": DataSource.objects.filter(is_active=True).count(),
        "visualizations": ProjectVisualization.objects.filter(is_active=True).count(),
    }

    return render(
        request,
        "dashboard/overview.html",
        {
            "dashboard_section": "overview",
            "metrics": metrics,
            "recent_projects": recent_projects,
        },
    )


def project_list(request):
    status_filter = request.GET.get("status", "all")
    if status_filter not in STATUS_FILTERS:
        status_filter = "all"

    active_data_sources_prefetch = Prefetch(
        "data_sources",
        queryset=DataSource.objects.filter(is_active=True).order_by("-uploaded_at"),
        to_attr="active_data_sources",
    )
    projects_qs = PortfolioProject.objects.select_related("project_type").prefetch_related(active_data_sources_prefetch)
    if status_filter != "all":
        projects_qs = projects_qs.filter(status=status_filter)

    projects = list(projects_qs.order_by("-updated_at"))
    project_types = list(ProjectType.objects.filter(is_active=True).order_by("name"))

    has_predictive = any(project_type.name.lower() == "modelo predictivo" for project_type in project_types)
    if not has_predictive:
        project_types.append(ProjectType(name="Modelo predictivo", slug="modelo-predictivo", is_active=True))

    grouped_projects = []
    for project_type in project_types:
        cards = []
        for project in projects:
            if project.project_type_id != project_type.id and project.project_type.name != project_type.name:
                continue

            main_dataset = project.active_data_sources[0] if project.active_data_sources else None
            cards.append(
                {
                    "title": project.title,
                    "question": project.question,
                    "status_label": STATUS_LABELS.get(project.status, project.status),
                    "main_dataset_name": main_dataset.name if main_dataset else "Sin dataset",
                    "slug": project.slug,
                }
            )

        grouped_projects.append(
            {
                "type_name": project_type.name,
                "cards": cards,
            }
        )

    return render(
        request,
        "dashboard/project_list.html",
        {
            "dashboard_section": "projects",
            "status_filter": status_filter,
            "grouped_projects": grouped_projects,
            "status_options": [
                ("all", "Todos"),
                (PortfolioProject.Status.DRAFT, "Borrador"),
                (PortfolioProject.Status.PUBLISHED, "Publicado"),
                (PortfolioProject.Status.ARCHIVED, "Archivado"),
            ],
        },
    )


def project_detail(request, slug):
    active_data_sources_prefetch = Prefetch(
        "data_sources",
        queryset=DataSource.objects.filter(is_active=True).order_by("-uploaded_at"),
        to_attr="active_data_sources",
    )
    active_visualizations_prefetch = Prefetch(
        "project_visualizations",
        queryset=ProjectVisualization.objects.filter(is_active=True).order_by("display_order", "id"),
        to_attr="active_visualizations",
    )

    project = get_object_or_404(
        PortfolioProject.objects.select_related("category", "project_type")
        .prefetch_related(active_data_sources_prefetch, active_visualizations_prefetch),
        slug=slug,
    )

    main_dataset = project.active_data_sources[0] if project.active_data_sources else None

    return render(
        request,
        "dashboard/project_detail.html",
        {
            "dashboard_section": "projects",
            "project": project,
            "status_label": STATUS_LABELS.get(project.status, project.status),
            "main_dataset": main_dataset,
            "datasets_count": len(project.active_data_sources),
            "visualizations_count": len(project.active_visualizations),
            "public_project_url": reverse("portfolio_projects:project_detail", kwargs={"slug": project.slug}),
        },
    )
