from django.urls import path

from . import views

app_name = "platform"

urlpatterns = [
    path("", views.home, name="home"),
    path("explorar/", views.project_explore, name="project_explore"),
    path("healthcheck/", views.healthcheck, name="healthcheck"),
]
