from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.urls import reverse

from apps.data_sources.models import DataSource
from apps.data_sources.services import extract_metadata
from apps.data_visualizations.engine import VisualizationEngineError, build_visualization_payload
from apps.data_visualizations.models import ProjectVisualization
from apps.dashboard.models import PublicProfile
from apps.portfolio_projects.models import PortfolioProject

from .dataset_columns import analyze_data_source_columns
from .forms import DataSourceEditForm, DataSourceUploadForm, ProjectCreateForm, PublicProfileForm, VisualizationCreateForm
from .services import build_overview_activity, build_project_publish_checklist

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


def _profile_form_page_context(*, form, page_title, page_heading, page_description, submit_label, cancel_url):
    return {
        "dashboard_section": "profile",
        "form": form,
        "page_title": page_title,
        "page_heading": page_heading,
        "page_description": page_description,
        "submit_label": submit_label,
        "cancel_url": cancel_url,
    }


def _visualization_form_page_context(
    *,
    form,
    project,
    data_source,
    page_title,
    page_heading,
    page_description,
    submit_label,
    cancel_url,
    context_label,
    preview_payload,
    preview_error,
):
    column_context = analyze_data_source_columns(data_source)

    return {
        "dashboard_section": "projects",
        "project": project,
        "data_source": data_source,
        "form": form,
        "page_title": page_title,
        "page_heading": page_heading,
        "page_description": page_description,
        "submit_label": submit_label,
        "cancel_url": cancel_url,
        "context_label": context_label,
        "status_label": STATUS_LABELS.get(project.status, project.status),
        "processing_status_label": DATA_SOURCE_STATUS_LABELS.get(data_source.processing_status, data_source.processing_status),
        "source_type_label": data_source.get_source_type_display(),
        "preview_payload": preview_payload,
        "preview_error": preview_error,
        **column_context,
    }


def _build_dashboard_metrics():
    return {
        "total_projects": 0,
        "published_projects": 0,
        "draft_projects": 0,
        "datasets": 0,
        "visualizations": 0,
    }


def _build_dashboard_metrics_for_owner(owner):
    if owner is None:
        return _build_dashboard_metrics()

    return {
        "total_projects": PortfolioProject.objects.filter(owner=owner).count(),
        "published_projects": PortfolioProject.objects.filter(owner=owner, status=PortfolioProject.Status.PUBLISHED).count(),
        "draft_projects": PortfolioProject.objects.filter(owner=owner, status=PortfolioProject.Status.DRAFT).count(),
        "datasets": DataSource.objects.filter(project__owner=owner, is_active=True).count(),
        "visualizations": ProjectVisualization.objects.filter(portfolio_project__owner=owner, is_active=True).count(),
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


def _build_dashboard_profile_context(user):
    try:
        profile = user.public_profile
    except ObjectDoesNotExist:
        profile = None
    avatar_url = profile.avatar_url if profile else ""

    display_name = user.get_full_name() or user.username or "Analista"
    headline = "Perfil público aún no configurado"
    bio = "Este perfil todavía no tiene una biografía pública visible."
    location = ""

    if profile:
        display_name = profile.display_name or display_name
        headline = profile.headline or headline
        bio = profile.bio or bio
        location = profile.location or ""

    return {
        "profile_available": profile is not None,
        "display_name": display_name,
        "headline": headline,
        "bio": bio,
        "location": location,
        "avatar_url": avatar_url,
        "avatar_initial": (display_name[:1] if display_name else "A").upper(),
    }


@login_required
def overview(request):
    owner = request.user
    active_data_sources_prefetch = Prefetch(
        "data_sources",
        queryset=DataSource.objects.filter(is_active=True).order_by("-uploaded_at"),
        to_attr="active_data_sources",
    )
    recent_projects = list(
        PortfolioProject.objects.filter(owner=owner)
        .select_related("project_type", "category")
        .prefetch_related(active_data_sources_prefetch)
        .order_by("-updated_at")[:6]
    )

    for project in recent_projects:
        project.status_label = STATUS_LABELS.get(project.status, project.status)
        main_dataset = project.active_data_sources[0] if project.active_data_sources else None
        project.main_dataset_name = main_dataset.name if main_dataset else "Sin dataset"

    metrics = _build_dashboard_metrics_for_owner(owner)
    activity_context = build_overview_activity(owner, recent_limit=3)
    analyst_profile = _build_dashboard_profile_context(owner)

    return render(
        request,
        "dashboard/overview.html",
        {
            "dashboard_section": "overview",
            "metrics": metrics,
            "recent_projects": recent_projects,
            "analyst_profile": analyst_profile,
            **activity_context,
        },
    )


@login_required
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
    projects_qs = PortfolioProject.objects.filter(owner=request.user).select_related("project_type", "category").prefetch_related(
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

    metrics = _build_dashboard_metrics_for_owner(request.user)

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


@login_required
def dataset_list(request):
    datasets_qs = (
        DataSource.objects.select_related("project")
        .filter(project__owner=request.user)
        .order_by("-uploaded_at")
    )
    datasets = list(datasets_qs)

    for ds in datasets:
        ds.processing_status_label = DATA_SOURCE_STATUS_LABELS.get(ds.processing_status, ds.processing_status)
        ds.source_type_label = ds.get_source_type_display()

    metrics = _build_dashboard_metrics_for_owner(request.user)

    return render(
        request,
        "dashboard/dataset_list.html",
        {
            "dashboard_section": "datasets",
            "datasets": datasets,
            "metrics": metrics,
        },
    )


@login_required
def profile_edit(request):
    if request.method == "POST":
        profile, _ = PublicProfile.objects.get_or_create(user=request.user)
        form = PublicProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, "Tu perfil público se actualizó correctamente.")
            return redirect("dashboard:profile_edit")
    else:
        profile = PublicProfile.objects.filter(user=request.user).first()
        if profile is None:
            profile = PublicProfile(user=request.user)
        form = PublicProfileForm(instance=profile)

    return render(
        request,
        "dashboard/profile_edit.html",
        _profile_form_page_context(
            form=form,
            page_title="Dashboard | Perfil público",
            page_heading="Perfil público",
            page_description="Edita la tarjeta pública que acompaña tu portafolio de proyectos.",
            submit_label="Guardar perfil público",
            cancel_url=reverse("dashboard:overview"),
        ),
    )


@login_required
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
        owner=request.user,
        slug=slug,
    )

    project_publish_checklist = build_project_publish_checklist(project)

    if request.method == "POST" and request.POST.get("action") == "publish_project" and project_publish_checklist["all_ready"]:
        project.status = PortfolioProject.Status.PUBLISHED
        project.save(update_fields=["status", "updated_at"])
        return redirect("dashboard:project_detail", slug=project.slug)

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
            "project_publish_checklist": project_publish_checklist,
        },
    )


@login_required
def project_create(request):
    if request.method == "POST":
        form = ProjectCreateForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
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


@login_required
def project_edit(request, slug):
    project = get_object_or_404(
        PortfolioProject.objects.select_related("category", "project_type"),
        owner=request.user,
        slug=slug,
    )

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


@login_required
def project_add_dataset(request, slug):
    project = get_object_or_404(PortfolioProject.objects.only("id", "slug", "title"), owner=request.user, slug=slug)

    if request.method == "POST":
        form = DataSourceUploadForm(request.POST, request.FILES)
        if form.is_valid():
            data_source = form.save(commit=False)
            data_source.project = project
            uploaded_file = form.cleaned_data.get("file")

            if data_source.source_type == DataSource.SourceType.GOOGLE_SHEETS:
                data_source.original_filename = "Google Sheets"
            elif uploaded_file:
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


@login_required
def dataset_detail(request, project_slug, dataset_id):
    project = get_object_or_404(PortfolioProject.objects.only("id", "slug", "title"), owner=request.user, slug=project_slug)
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


def _check_visualization_column_mismatches(data_source):
    if not data_source.columns_schema or "columns" not in data_source.columns_schema:
        return []

    columns = data_source.columns_schema.get("columns", [])
    column_names = {col.get("name") for col in columns if "name" in col}

    active_visualizations = data_source.project_visualizations.filter(is_active=True)
    warnings = []
    for vis in active_visualizations:
        vis_warnings = []
        if vis.x_axis_column and vis.x_axis_column not in column_names:
            vis_warnings.append(f"eje X '{vis.x_axis_column}'")
        if vis.y_axis_column and vis.y_axis_column not in column_names:
            vis_warnings.append(f"eje Y '{vis.y_axis_column}'")

        if vis_warnings:
            warnings.append(
                f"La visualización '{vis.title}' (ID {vis.id}) hace referencia a {', '.join(vis_warnings)} que ya no existe en el dataset."
            )
    return warnings


@login_required
def dataset_edit(request, project_slug, dataset_id):
    project = get_object_or_404(PortfolioProject.objects.only("id", "slug", "title"), owner=request.user, slug=project_slug)
    data_source = get_object_or_404(
        DataSource.objects.select_related("project"),
        pk=dataset_id,
        project=project,
    )

    action = request.POST.get("action", "save") if request.method == "POST" else "view"

    if request.method == "POST":
        if action == "reprocess":
            # Re-process current file
            try:
                columns_schema = extract_metadata(data_source)
                data_source.columns_schema = columns_schema
                data_source.row_count = columns_schema.get("row_count")
                data_source.processing_status = DataSource.ProcessingStatus.PROCESSED
                data_source.processing_error = ""
                messages.success(request, f"La metadata de {data_source.name} ha sido re-procesada exitosamente.")
            except Exception as exc:
                data_source.columns_schema = {}
                data_source.row_count = None
                data_source.processing_status = DataSource.ProcessingStatus.FAILED
                data_source.processing_error = f"La extracción de metadata falló: {exc}"
                messages.error(request, f"Error al re-procesar metadata: {exc}")

            data_source.save(
                update_fields=[
                    "columns_schema",
                    "row_count",
                    "processing_status",
                    "processing_error",
                    "updated_at",
                ]
            )

            # Check for visualization column mismatches after reprocessing
            warnings = _check_visualization_column_mismatches(data_source)
            for warning in warnings:
                messages.warning(request, warning)

            return redirect("dashboard:dataset_detail", project_slug=project.slug, dataset_id=data_source.id)

        else:
            form = DataSourceEditForm(request.POST, request.FILES, instance=data_source)
            if form.is_valid():
                ds = form.save(commit=False)
                new_file = form.cleaned_data.get("file")

                # Check if file is being replaced
                file_replaced = False
                if new_file:
                    ds.original_filename = new_file.name.rsplit("/", 1)[-1]
                    ds.processing_status = DataSource.ProcessingStatus.PENDING
                    ds.processing_error = ""
                    file_replaced = True
                elif ds.source_type == DataSource.SourceType.GOOGLE_SHEETS and ("source_url" in form.changed_data or "source_type" in form.changed_data):
                    ds.original_filename = "Google Sheets"
                    ds.processing_status = DataSource.ProcessingStatus.PENDING
                    ds.processing_error = ""
                    file_replaced = True

                ds.save()

                if file_replaced:
                    try:
                        columns_schema = extract_metadata(ds)
                        ds.columns_schema = columns_schema
                        ds.row_count = columns_schema.get("row_count")
                        ds.processing_status = DataSource.ProcessingStatus.PROCESSED
                        ds.processing_error = ""
                        messages.success(request, "La fuente de datos ha sido actualizada y la metadata procesada exitosamente.")
                    except Exception as exc:
                        ds.columns_schema = {}
                        ds.row_count = None
                        ds.processing_status = DataSource.ProcessingStatus.FAILED
                        ds.processing_error = f"La extracción de metadata falló: {exc}"
                        messages.error(request, f"Error al extraer metadata de la fuente de datos: {exc}")

                    ds.save(
                        update_fields=[
                            "original_filename",
                            "columns_schema",
                            "row_count",
                            "processing_status",
                            "processing_error",
                            "updated_at",
                        ]
                    )

                    # Check for visualization column mismatches after replacing file
                    warnings = _check_visualization_column_mismatches(ds)
                    for warning in warnings:
                        messages.warning(request, warning)
                else:
                    messages.success(request, f"El dataset {ds.name} ha sido actualizado correctamente.")

                return redirect("dashboard:dataset_detail", project_slug=project.slug, dataset_id=ds.id)
    else:
        form = DataSourceEditForm(instance=data_source)

    return render(
        request,
        "dashboard/dataset_create.html",
        {
            "dashboard_section": "projects",
            "project": project,
            "data_source": data_source,
            "form": form,
            "page_title": f"Dashboard | Editar dataset {data_source.name}",
            "page_heading": "Editar dataset",
            "page_description": "Modifica las opciones básicas del dataset o reemplaza el archivo fuente.",
            "submit_label": "Guardar cambios",
            "cancel_url": reverse("dashboard:dataset_detail", kwargs={"project_slug": project.slug, "dataset_id": data_source.id}),
            "is_edit": True,
        },
    )


@login_required
def visualization_create(request, project_slug, dataset_id):
    project = get_object_or_404(PortfolioProject.objects.only("id", "slug", "title"), owner=request.user, slug=project_slug)
    data_source = get_object_or_404(
        DataSource.objects.select_related("project"),
        pk=dataset_id,
        project=project,
    )

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
        _visualization_form_page_context(
            form=form,
            project=project,
            data_source=data_source,
            page_title=f"Dashboard | Nueva visualización para {data_source.name}",
            page_heading="Nueva visualización",
            page_description="Crea una visualización a partir de las columnas detectadas en este dataset.",
            submit_label="Crear visualización",
            cancel_url=reverse("dashboard:dataset_detail", kwargs={"project_slug": project.slug, "dataset_id": data_source.id}),
            context_label="Nueva visualización para:",
            preview_payload=preview_payload,
            preview_error=preview_error,
        ),
    )


@login_required
def visualization_edit(request, project_slug, visualization_id):
    project = get_object_or_404(PortfolioProject.objects.only("id", "slug", "title"), owner=request.user, slug=project_slug)
    visualization = get_object_or_404(
        ProjectVisualization.objects.select_related("portfolio_project", "source_dataset"),
        pk=visualization_id,
        portfolio_project=project,
    )
    data_source = visualization.source_dataset

    preview_payload = None
    preview_error = ""

    if request.method == "POST":
        form = VisualizationCreateForm(request.POST, instance=visualization, data_source=data_source)
        action = request.POST.get("action", "save")
        if form.is_valid():
            updated_visualization = form.save(commit=False)
            updated_visualization.portfolio_project = project
            updated_visualization.source_dataset = data_source

            try:
                preview_payload = build_visualization_payload(updated_visualization)
            except VisualizationEngineError as exc:
                preview_error = str(exc)
                form.add_error(None, preview_error)
            else:
                if action == "preview":
                    pass
                else:
                    updated_visualization.save()
                    return redirect("dashboard:project_detail", slug=project.slug)
    else:
        form = VisualizationCreateForm(
            instance=visualization,
            data_source=data_source,
            initial={
                "display_order": visualization.display_order,
                "is_active": visualization.is_active,
            },
        )

    return render(
        request,
        "dashboard/visualization_create.html",
        _visualization_form_page_context(
            form=form,
            project=project,
            data_source=data_source,
            page_title=f"Dashboard | Editar visualización {visualization.title}",
            page_heading="Editar visualización",
            page_description="Actualiza la configuración guardada de esta visualización sin cambiar su fuente de datos.",
            submit_label="Guardar cambios",
            cancel_url=reverse("dashboard:project_detail", kwargs={"slug": project.slug}),
            context_label="Editar visualización de:",
            preview_payload=preview_payload,
            preview_error=preview_error,
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
