from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.urls import reverse

from apps.data_sources.models import DataSource
from apps.data_sources.services import extract_metadata
from apps.data_visualizations.models import ProjectVisualization
from apps.portfolio_projects.models import PortfolioProject

from .forms import DataSourceUploadForm, ProjectCreateForm

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


def is_recommendable_column(column, row_count):
    column_name = str(column.get("name", "")).strip()
    if not column_name:
        return False

    if column_name.startswith("Unnamed"):
        return False

    if column_name in {"Delete", "ID2"}:
        return False

    null_count = column.get("null_count")
    if row_count is not None and null_count is not None and null_count == row_count:
        return False

    column_type = str(column.get("type", "unknown")).strip().lower()
    sample_values = column.get("sample_values") if isinstance(column.get("sample_values"), list) else []
    unique_count = column.get("unique_count")
    has_useful_values = bool(sample_values) or unique_count not in (None, 0)

    if column_type == "unknown" and not has_useful_values:
        return False

    return True


def _build_project_data_source_context(data_source):
    processing_status_label = DATA_SOURCE_STATUS_LABELS.get(data_source.processing_status, data_source.processing_status)
    source_type_label = data_source.get_source_type_display()
    columns_schema = data_source.columns_schema if isinstance(data_source.columns_schema, dict) else {}
    raw_columns = columns_schema.get("columns") if isinstance(columns_schema.get("columns"), list) else []
    row_count = data_source.row_count if isinstance(data_source.row_count, int) else None

    columns = []
    summary = {
        "total_columns": 0,
        "numeric_columns": 0,
        "categorical_columns": 0,
        "datetime_columns": 0,
        "nullable_columns": 0,
    }
    x_axis_columns = []
    y_axis_columns = []

    for raw_column in raw_columns:
        if not isinstance(raw_column, dict):
            continue

        column_type = str(raw_column.get("type", "unknown")).strip().lower()
        column_name = raw_column.get("name") or "Sin nombre"
        nullable = bool(raw_column.get("nullable"))
        null_count = raw_column.get("null_count")

        column = {
            "name": column_name,
            "type": column_type,
            "original_dtype": raw_column.get("original_dtype", "Desconocido"),
            "nullable": nullable,
            "null_count": null_count if null_count is not None else 0,
            "unique_count": raw_column.get("unique_count"),
            "min": raw_column.get("min"),
            "max": raw_column.get("max"),
            "sample_values": raw_column.get("sample_values") if isinstance(raw_column.get("sample_values"), list) else [],
        }
        columns.append(column)

        summary["total_columns"] += 1
        if column["type"] == "numeric":
            summary["numeric_columns"] += 1
        if column["type"] == "categorical":
            summary["categorical_columns"] += 1
        if column["type"] == "datetime":
            summary["datetime_columns"] += 1
        if nullable or (isinstance(null_count, int) and null_count > 0):
            summary["nullable_columns"] += 1

        if not is_recommendable_column(column, row_count):
            continue

        if column["type"] == "numeric":
            y_axis_columns.append(column)
        if column["type"] == "categorical":
            x_axis_columns.append(column)
        if column["type"] == "datetime":
            x_axis_columns.append(column)
        if column["type"] == "text":
            x_axis_columns.append(column)

    return {
        "processing_status_label": processing_status_label,
        "source_type_label": source_type_label,
        "columns_schema": columns_schema,
        "columns": columns,
        "summary": summary,
        "x_axis_columns": x_axis_columns,
        "y_axis_columns": y_axis_columns,
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
    data_sources_prefetch = Prefetch(
        "data_sources",
        queryset=DataSource.objects.order_by("-uploaded_at"),
        to_attr="project_data_sources",
    )
    active_visualizations_prefetch = Prefetch(
        "project_visualizations",
        queryset=ProjectVisualization.objects.filter(is_active=True).order_by("display_order", "id"),
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


def _build_unique_slug(title):
    base_slug = slugify(title) or "proyecto"
    candidate = base_slug
    index = 2

    while PortfolioProject.objects.filter(slug=candidate).exists():
        candidate = f"{base_slug}-{index}"
        index += 1

    return candidate
