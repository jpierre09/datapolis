import json

from django.shortcuts import get_object_or_404, render

from apps.data_visualizations.engine.builder import build_visualization_payload
from apps.data_visualizations.engine.exceptions import VisualizationEngineError
from apps.data_visualizations.models import ProjectVisualization

from .models import PortfolioProject


def project_list(request):
	projects = (
		PortfolioProject.objects.filter(status=PortfolioProject.Status.PUBLISHED)
		.select_related("category", "project_type", "owner")
		.order_by("-created_at")
	)
	return render(request, "portfolio_projects/project_list.html", {"projects": projects})


def project_detail(request, slug):
	project = get_object_or_404(
		PortfolioProject.objects.select_related("category", "project_type", "owner"),
		slug=slug,
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
					"payload_json": json.dumps(payload),
					"error": "",
				}
			)
		except VisualizationEngineError as exc:
			visualization_payloads.append(
				{
					"visualization": visualization,
					"payload": None,
					"payload_json": "",
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
		},
	)
