from django.contrib import admin

from .models import PublicProfile

@admin.register(PublicProfile)
class PublicProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "slug", "headline", "location")
    search_fields = ("user__username", "display_name", "slug", "headline")
    readonly_fields = ("slug",)
