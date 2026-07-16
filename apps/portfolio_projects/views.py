from django.shortcuts import get_object_or_404, redirect, render

from apps.data_visualizations.engine.builder import build_visualization_payload
from apps.data_visualizations.engine.exceptions import VisualizationEngineError
from apps.data_visualizations.models import ProjectVisualization
from apps.dashboard.models import PublicProfile
from .models import PortfolioProject, ProjectCategory


def _get_user_public_profile(user):
	if user is None or not hasattr(user, "public_profile"):
		return None
	return user.public_profile


def _normalize_external_links(external_links):
	links = []
	if isinstance(external_links, dict):
		for label, url in external_links.items():
			if not url:
				continue
			links.append({"label": str(label).replace("_", " ").strip().title(), "url": url})
	elif isinstance(external_links, list):
		for item in external_links:
			if isinstance(item, dict) and item.get("url"):
				links.append({
					"label": str(item.get("label") or item.get("name") or item["url"]).strip().title(),
					"url": item["url"],
				})
	return links


def _build_public_profile_context(user):
	profile = _get_user_public_profile(user)
	avatar_url = profile.avatar_url if profile else ""

	display_name = "Analista"
	headline = "Perfil público aún no configurado"
	bio = "Este portafolio todavía no tiene una biografía pública visible."
	location = ""
	skills = []
	links = []
	profile_available = profile is not None

	if user:
		display_name = user.get_full_name() or user.username or display_name

	if profile:
		display_name = profile.display_name or display_name
		headline = profile.headline or headline
		bio = profile.bio or bio
		location = profile.location or ""
		skills = [str(skill).strip() for skill in (profile.skills or []) if str(skill).strip()]
		links = _normalize_external_links(profile.external_links)

	return {
		"profile_available": profile_available,
		"display_name": display_name,
		"headline": headline,
		"bio": bio,
		"location": location,
		"skills": skills,
		"links": links,
		"avatar_url": avatar_url,
	}


def project_list(request):
	from django.contrib.auth import get_user_model
	User = get_user_model()
	principal_user = User.objects.filter(
		public_profile__isnull=False,
	).exclude(public_profile__slug="").order_by("-is_superuser", "id").first()

	if principal_user:
		return redirect("public_profile_detail", slug=principal_user.public_profile.slug)

	projects = (
		PortfolioProject.objects.filter(status=PortfolioProject.Status.PUBLISHED)
		.select_related("category", "project_type", "owner", "owner__public_profile")
		.order_by("-created_at")
	)

	# Group projects by category
	categories_with_projects = []
	categories = ProjectCategory.objects.all().order_by("name")

	for category in categories:
		cat_projects = [p for p in projects if p.category_id == category.id]
		if cat_projects:
			categories_with_projects.append({
				"category": category,
				"projects": cat_projects
			})

	portfolio_owner = projects[0].owner if projects else None
	portfolio_profile = _build_public_profile_context(portfolio_owner)

	# Look for any projects that don't fall into ProjectCategory queried (just in case)
	# Though ProjectCategory is a ForeignKey on PortfolioProject, so they must have one.

	return render(
		request,
		"portfolio_projects/project_list.html",
		{
			"projects": projects,
			"categories_with_projects": categories_with_projects,
			"portfolio_profile": portfolio_profile,
		}
	)


def project_detail(request, slug):
	project = get_object_or_404(
		PortfolioProject.objects.select_related("category", "project_type", "owner", "owner__public_profile"),
		slug=slug,
		status=PortfolioProject.Status.PUBLISHED,
	)

	if hasattr(project.owner, "public_profile") and project.owner.public_profile.slug:
		return redirect("public_profile_project_detail", profile_slug=project.owner.public_profile.slug, project_slug=project.slug)

	data_sources = project.data_sources.filter(is_active=True).order_by("-uploaded_at")
	visualizations = (
		ProjectVisualization.objects.filter(portfolio_project=project, is_active=True)
		.select_related("source_dataset")
		.order_by("display_order", "id")
	)

	visualization_payloads = []
	for visualization in visualizations:
		try:
			payload = build_visualization_payload(visualization)
			visualization_payloads.append(
				{
					"visualization": visualization,
					"payload": payload,
					"payload_script_id": f"payload-{visualization.id}",
					"error": "",
				}
			)
		except VisualizationEngineError as exc:
			visualization_payloads.append(
				{
					"visualization": visualization,
					"payload": None,
					"payload_script_id": "",
					"error": str(exc),
				}
			)

	return render(
		request,
		"portfolio_projects/project_detail.html",
		{
			"project": project,
			"data_sources": data_sources,
			"visualization_payloads": visualization_payloads,
			"project_profile": _build_public_profile_context(project.owner),
		},
	)

def public_profile_detail(request, slug):
	public_profile = get_object_or_404(
		PublicProfile.objects.select_related("user"),
		slug=slug,
	)

	projects = (
		PortfolioProject.objects.filter(
			status=PortfolioProject.Status.PUBLISHED,
			owner=public_profile.user,
		)
		.select_related("category", "project_type", "owner", "owner__public_profile")
		.order_by("-created_at")
	)

	categories_with_projects = []
	categories = ProjectCategory.objects.all().order_by("name")

	for category in categories:
		cat_projects = [p for p in projects if p.category_id == category.id]
		if cat_projects:
			categories_with_projects.append({
				"category": category,
				"projects": cat_projects,
			})

	portfolio_profile = _build_public_profile_context(public_profile.user)

	return render(
		request,
		"portfolio_projects/project_list.html",
		{
			"projects": projects,
			"categories_with_projects": categories_with_projects,
			"portfolio_profile": portfolio_profile,
			"public_profile": public_profile,
			"is_user_portfolio": True,
		}
	)


def public_profile_project_detail(request, profile_slug, project_slug):
	public_profile = get_object_or_404(
		PublicProfile.objects.select_related("user"),
		slug=profile_slug,
	)

	project = get_object_or_404(
		PortfolioProject.objects.select_related("category", "project_type", "owner", "owner__public_profile"),
		slug=project_slug,
		owner=public_profile.user,
		status=PortfolioProject.Status.PUBLISHED,
	)

	data_sources = project.data_sources.filter(is_active=True).order_by("-uploaded_at")
	visualizations = (
		ProjectVisualization.objects.filter(portfolio_project=project, is_active=True)
		.select_related("source_dataset")
		.order_by("display_order", "id")
	)

	visualization_payloads = []
	for visualization in visualizations:
		try:
			payload = build_visualization_payload(visualization)
			visualization_payloads.append(
				{
					"visualization": visualization,
					"payload": payload,
					"payload_script_id": f"payload-{visualization.id}",
					"error": "",
				}
			)
		except VisualizationEngineError as exc:
			visualization_payloads.append(
				{
					"visualization": visualization,
					"payload": None,
					"payload_script_id": "",
					"error": str(exc),
				}
			)

	return render(
		request,
		"portfolio_projects/project_detail.html",
		{
			"project": project,
			"data_sources": data_sources,
			"visualization_payloads": visualization_payloads,
			"project_profile": _build_public_profile_context(project.owner),
		},
	)
