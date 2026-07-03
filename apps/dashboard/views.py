from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.urls import reverse

from apps.data_sources.models import DataSource
from apps.data_visualizations.models import ProjectVisualization
from apps.portfolio_projects.models import PortfolioProject

from .forms import ProjectCreateForm

STATUS_LABELS = {
    PortfolioProject.Status.DRAFT: "Borrador",
    PortfolioProject.Status.PUBLISHED: "Publicado",
    PortfolioProject.Status.ARCHIVED: "Archivado",
}
STATUS_FILTERS = {"all", PortfolioProject.Status.DRAFT, PortfolioProject.Status.PUBLISHED, PortfolioProject.Status.ARCHIVED}


def _project_form_page_context(*, form, page_title, page_heading, page_description, submit_label, cancel_url, status_note):
    return {
        "dashboard_section": "projects",
        "form": form,
        "page_title": page_title,
        "page_heading": page_heading,
        "page_description": page_description,
        "submit_label": submit_label,
        "cancel_url": cancel_url,
        "status_note": status_note,
    }


def _build_dashboard_metrics():
    return {
        "total_projects": PortfolioProject.objects.count(),
        "published_projects": PortfolioProject.objects.filter(status=PortfolioProject.Status.PUBLISHED).count(),
        "draft_projects": PortfolioProject.objects.filter(status=PortfolioProject.Status.DRAFT).count(),
        "datasets": DataSource.objects.filter(is_active=True).count(),
        "visualizations": ProjectVisualization.objects.filter(is_active=True).count(),
    }


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

    metrics = _build_dashboard_metrics()

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
    active_visualizations_prefetch = Prefetch(
        "project_visualizations",
        queryset=ProjectVisualization.objects.filter(is_active=True).order_by("display_order", "id"),
        to_attr="active_visualizations",
    )
    projects_qs = PortfolioProject.objects.select_related("project_type", "category").prefetch_related(
        active_data_sources_prefetch,
        active_visualizations_prefetch,
    )
    if status_filter != "all":
        projects_qs = projects_qs.filter(status=status_filter)

    projects = list(projects_qs.order_by("-updated_at"))

    for project in projects:
        project.status_label = STATUS_LABELS.get(project.status, project.status)
        main_dataset = project.active_data_sources[0] if project.active_data_sources else None
        project.main_dataset_name = main_dataset.name if main_dataset else "Sin dataset"
        project.visualizations_count = len(project.active_visualizations)

    metrics = _build_dashboard_metrics()

    return render(
        request,
        "dashboard/project_list.html",
        {
            "dashboard_section": "projects",
            "status_filter": status_filter,
            "projects": projects,
            "metrics": metrics,
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
        },
    )


def project_create(request):
    if request.method == "POST":
        form = ProjectCreateForm(request.POST)
        if form.is_valid():
            user = request.user if request.user.is_authenticated else get_user_model().objects.order_by("id").first()
            if not user:
                form.add_error(None, "No hay usuarios disponibles para asignar el proyecto.")
            else:
                project = form.save(commit=False)
                project.owner = user
                project.slug = _build_unique_slug(project.title)
                project.save()
                return redirect("dashboard:project_detail", slug=project.slug)
    else:
        form = ProjectCreateForm()

    return render(
        request,
        "dashboard/project_create.html",
        _project_form_page_context(
            form=form,
            page_title="Dashboard | Nuevo proyecto",
            page_heading="Nuevo proyecto",
            page_description="Registra la base de un proyecto analítico para convertirlo en una historia visual y publicable.",
            submit_label="Crear proyecto",
            cancel_url=reverse("dashboard:project_list"),
            status_note="Estado del proyecto: Borrador",
        ),
    )


def project_edit(request, slug):
    project = get_object_or_404(PortfolioProject.objects.select_related("category", "project_type"), slug=slug)

    if request.method == "POST":
        form = ProjectCreateForm(request.POST, instance=project)
        if form.is_valid():
            updated_project = form.save()
            return redirect("dashboard:project_detail", slug=updated_project.slug)
    else:
        form = ProjectCreateForm(instance=project)

    return render(
        request,
        "dashboard/project_create.html",
        _project_form_page_context(
            form=form,
            page_title=f"Dashboard | Editar {project.title}",
            page_heading="Editar proyecto",
            page_description="Actualiza la base del proyecto, su clasificación y su estado de avance.",
            submit_label="Guardar cambios",
            cancel_url=reverse("dashboard:project_detail", kwargs={"slug": project.slug}),
            status_note=f"Estado actual: {STATUS_LABELS.get(project.status, project.status)}",
        ),
    )


def _build_unique_slug(title):
    base_slug = slugify(title) or "proyecto"
    candidate = base_slug
    index = 2

    while PortfolioProject.objects.filter(slug=candidate).exists():
        candidate = f"{base_slug}-{index}"
        index += 1

    return candidate
