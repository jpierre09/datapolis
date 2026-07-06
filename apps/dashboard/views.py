from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.urls import reverse

from apps.data_sources.models import DataSource
from apps.data_sources.services import extract_metadata
from apps.data_visualizations.engine import VisualizationEngineError, build_visualization_payload
from apps.data_visualizations.models import ProjectVisualization
from apps.portfolio_projects.models import PortfolioProject

from .dataset_columns import analyze_data_source_columns
from .forms import DataSourceUploadForm, ProjectCreateForm, VisualizationCreateForm
from .services import build_overview_activity

STATUS_LABELS = {
    PortfolioProject.Status.DRAFT: "Borrador",
    PortfolioProject.Status.PUBLISHED: "Publicado",
    PortfolioProject.Status.ARCHIVED: "Archivado",
}
STATUS_FILTERS = {"all", PortfolioProject.Status.DRAFT, PortfolioProject.Status.PUBLISHED, PortfolioProject.Status.ARCHIVED}
DATA_SOURCE_STATUS_LABELS = {
    DataSource.ProcessingStatus.PENDING: "Pendiente",
    DataSource.ProcessingStatus.PROCESSED: "Procesado",
    DataSource.ProcessingStatus.FAILED: "Fallido",
}


def _build_project_data_source_context(data_source):
    processing_status_label = DATA_SOURCE_STATUS_LABELS.get(data_source.processing_status, data_source.processing_status)
    source_type_label = data_source.get_source_type_display()
    column_context = analyze_data_source_columns(data_source)

    return {
        "processing_status_label": processing_status_label,
        "source_type_label": source_type_label,
        **column_context,
    }


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


def _build_visualization_preview_context(visualization):
    preview_payload = None
    preview_error = ""

    try:
        preview_payload = build_visualization_payload(visualization)
    except VisualizationEngineError:
        preview_error = "No se pudo generar la vista previa"
    except Exception:
        preview_error = "No se pudo generar la vista previa"

    return preview_payload, preview_error


def _get_dashboard_owner():
    user = get_user_model().objects.order_by("id").first()
    return user


def overview(request):
    owner = request.user if request.user.is_authenticated else _get_dashboard_owner()
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
    activity_context = build_overview_activity(owner, recent_limit=3)

    return render(
        request,
        "dashboard/overview.html",
        {
            "dashboard_section": "overview",
            "metrics": metrics,
            "recent_projects": recent_projects,
            **activity_context,
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
    data_sources_prefetch = Prefetch(
        "data_sources",
        queryset=DataSource.objects.order_by("-uploaded_at"),
        to_attr="project_data_sources",
    )
    active_visualizations_prefetch = Prefetch(
        "project_visualizations",
        queryset=ProjectVisualization.objects.filter(is_active=True)
        .select_related("source_dataset")
        .order_by("display_order", "id"),
        to_attr="active_visualizations",
    )

    project = get_object_or_404(
        PortfolioProject.objects.select_related("category", "project_type")
        .prefetch_related(data_sources_prefetch, active_visualizations_prefetch),
        slug=slug,
    )

    main_dataset = project.project_data_sources[0] if project.project_data_sources else None

    for data_source in project.project_data_sources:
        data_source.processing_status_label = DATA_SOURCE_STATUS_LABELS.get(data_source.processing_status, data_source.processing_status)
        data_source.source_type_label = data_source.get_source_type_display()

    for visualization in project.active_visualizations:
        visualization.preview_payload_script_id = f"project-visualization-preview-payload-{visualization.id}"
        visualization.preview_payload, visualization.preview_error = _build_visualization_preview_context(visualization)
        visualization.preview_has_error = bool(visualization.preview_error)

    return render(
        request,
        "dashboard/project_detail.html",
        {
            "dashboard_section": "projects",
            "project": project,
            "status_label": STATUS_LABELS.get(project.status, project.status),
            "main_dataset": main_dataset,
            "datasets_count": len(project.project_data_sources),
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


def project_add_dataset(request, slug):
    project = get_object_or_404(PortfolioProject.objects.only("id", "slug", "title"), slug=slug)

    if request.method == "POST":
        form = DataSourceUploadForm(request.POST, request.FILES)
        if form.is_valid():
            data_source = form.save(commit=False)
            data_source.project = project
            uploaded_file = form.cleaned_data["file"]
            data_source.original_filename = uploaded_file.name.rsplit("/", 1)[-1]
            data_source.processing_status = DataSource.ProcessingStatus.PENDING
            data_source.processing_error = ""
            data_source.save()

            try:
                columns_schema = extract_metadata(data_source)
                data_source.columns_schema = columns_schema
                data_source.row_count = columns_schema.get("row_count")
                data_source.processing_status = DataSource.ProcessingStatus.PROCESSED
                data_source.processing_error = ""
            except Exception as exc:
                data_source.columns_schema = {}
                data_source.row_count = None
                data_source.processing_status = DataSource.ProcessingStatus.FAILED
                data_source.processing_error = f"La extracción de metadata falló: {exc}"

            data_source.save(
                update_fields=[
                    "original_filename",
                    "columns_schema",
                    "row_count",
                    "processing_status",
                    "processing_error",
                    "updated_at",
                ]
            )
            return redirect("dashboard:project_detail", slug=project.slug)
    else:
        form = DataSourceUploadForm()

    return render(
        request,
        "dashboard/dataset_create.html",
        {
            "dashboard_section": "projects",
            "project": project,
            "form": form,
            "page_title": f"Dashboard | Agregar dataset a {project.title}",
            "page_heading": "Agregar dataset",
            "page_description": "Sube un CSV o Excel para asociarlo al proyecto y procesar su metadata.",
            "submit_label": "Guardar dataset",
            "cancel_url": reverse("dashboard:project_detail", kwargs={"slug": project.slug}),
        },
    )


def dataset_detail(request, project_slug, dataset_id):
    project = get_object_or_404(PortfolioProject.objects.only("id", "slug", "title"), slug=project_slug)
    data_source = get_object_or_404(
        DataSource.objects.select_related("project"),
        pk=dataset_id,
        project=project,
    )

    data_source_context = _build_project_data_source_context(data_source)

    return render(
        request,
        "dashboard/dataset_detail.html",
        {
            "dashboard_section": "projects",
            "project": project,
            "data_source": data_source,
            "status_label": STATUS_LABELS.get(project.status, project.status),
            **data_source_context,
        },
    )


def visualization_create(request, project_slug, dataset_id):
    project = get_object_or_404(PortfolioProject.objects.only("id", "slug", "title"), slug=project_slug)
    data_source = get_object_or_404(
        DataSource.objects.select_related("project"),
        pk=dataset_id,
        project=project,
    )

    column_context = analyze_data_source_columns(data_source)
    preview_payload = None
    preview_error = ""

    if request.method == "POST":
        form = VisualizationCreateForm(request.POST, data_source=data_source)
        action = request.POST.get("action", "create")
        if form.is_valid():
            visualization = form.save(commit=False)
            visualization.portfolio_project = project
            visualization.source_dataset = data_source

            try:
                preview_payload = build_visualization_payload(visualization)
            except VisualizationEngineError as exc:
                preview_error = str(exc)
                form.add_error(None, preview_error)
            else:
                if action == "preview":
                    pass
                else:
                    visualization.save()
                    return redirect("dashboard:project_detail", slug=project.slug)
    else:
        form = VisualizationCreateForm(
            data_source=data_source,
            initial={
                "display_order": project.project_visualizations.count() + 1,
                "is_active": True,
            },
        )

    return render(
        request,
        "dashboard/visualization_create.html",
        {
            "dashboard_section": "projects",
            "project": project,
            "data_source": data_source,
            "form": form,
            "page_title": f"Dashboard | Nueva visualización para {data_source.name}",
            "page_heading": "Nueva visualización",
            "page_description": "Crea una visualización a partir de las columnas detectadas en este dataset.",
            "submit_label": "Crear visualización",
            "cancel_url": reverse("dashboard:dataset_detail", kwargs={"project_slug": project.slug, "dataset_id": data_source.id}),
            "status_label": STATUS_LABELS.get(project.status, project.status),
            "processing_status_label": DATA_SOURCE_STATUS_LABELS.get(data_source.processing_status, data_source.processing_status),
            "source_type_label": data_source.get_source_type_display(),
            "preview_payload": preview_payload,
            "preview_error": preview_error,
            **column_context,
        },
    )


def _build_unique_slug(title):
    base_slug = slugify(title) or "proyecto"
    candidate = base_slug
    index = 2

    while PortfolioProject.objects.filter(slug=candidate).exists():
        candidate = f"{base_slug}-{index}"
        index += 1

    return candidate
