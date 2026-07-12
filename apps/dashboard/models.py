from django.conf import settings
from django.db import models


class PublicProfile(models.Model):
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="public_profile",
	)
	display_name = models.CharField(max_length=255, blank=True)
	headline = models.CharField(max_length=255, blank=True)
	bio = models.TextField(blank=True)
	location = models.CharField(max_length=255, blank=True)
	external_links = models.JSONField(default=dict, blank=True)
	skills = models.JSONField(default=list, blank=True)
	avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)

	def __str__(self):
		return self.display_name or self.user.username
