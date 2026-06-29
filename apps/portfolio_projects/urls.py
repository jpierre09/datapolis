from django.urls import path

from . import views

app_name = "portfolio_projects"

urlpatterns = [
    path("", views.project_list, name="project_list"),
    path("<slug:slug>/", views.project_detail, name="project_detail"),
]
