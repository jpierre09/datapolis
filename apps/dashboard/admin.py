from django.contrib import admin

from .models import PublicProfile

@admin.register(PublicProfile)
class PublicProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "headline", "location")
