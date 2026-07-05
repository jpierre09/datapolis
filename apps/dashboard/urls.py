from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.overview, name="overview"),
    path("projects/", views.project_list, name="project_list"),
    path("projects/new/", views.project_create, name="project_create"),
    path("projects/<slug:slug>/edit/", views.project_edit, name="project_edit"),
    path("projects/<slug:slug>/datasets/new/", views.project_add_dataset, name="project_add_dataset"),
    path("projects/<slug:project_slug>/datasets/<int:dataset_id>/", views.dataset_detail, name="dataset_detail"),
    path("projects/<slug:slug>/", views.project_detail, name="project_detail"),
]
