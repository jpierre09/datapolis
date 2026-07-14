from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class PublicProfile(models.Model):
	user = models.OneToOneField(
		User,
		on_delete=models.CASCADE,
		related_name="public_profile",
	)
	slug = models.SlugField(max_length=100, unique=True, blank=True)
	display_name = models.CharField(max_length=255, blank=True)
	headline = models.CharField(max_length=255, blank=True)
	bio = models.TextField(blank=True)
	location = models.CharField(max_length=255, blank=True)
	external_links = models.JSONField(default=dict, blank=True)
	skills = models.JSONField(default=list, blank=True)
	avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)

	def __str__(self):
		return self.display_name or self.user.username

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = self._generate_unique_slug()
		super().save(*args, **kwargs)

	def _generate_unique_slug(self):
		base_value = (
			self.display_name
			or self.user.get_full_name()
			or self.user.username
			or "user"
		)
		base_slug = slugify(base_value) or "user"
		slug = base_slug
		counter = 2

		while PublicProfile.objects.filter(slug=slug).exclude(pk=self.pk).exists():
			slug = f"{base_slug}-{counter}"
			counter += 1
		return slug

