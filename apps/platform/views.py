from django.http import HttpResponse
from django.shortcuts import render


def home(request):
	return render(request, "public_pages/home.html")


def healthcheck(request):
	return HttpResponse("ok", content_type="text/plain")
