from django.db import migrations, models
from django.utils.text import slugify


def populate_public_profile_slugs(apps, schema_editor):
    PublicProfile = apps.get_model("dashboard", "PublicProfile")

    used_slugs = set(
        PublicProfile.objects.exclude(slug__isnull=True)
        .exclude(slug="")
        .values_list("slug", flat=True)
    )

    for profile in PublicProfile.objects.select_related("user").all():
        if profile.slug:
            continue

        user = profile.user
        full_name = f"{user.first_name} {user.last_name}".strip()

        base_value = (
            profile.display_name
            or full_name
            or user.username
            or f"user-{profile.pk}"
        )

        base_slug = slugify(base_value) or f"user-{profile.pk}"
        slug = base_slug
        counter = 2

        while slug in used_slugs:
            slug = f"{base_slug}-{counter}"
            counter += 1

        profile.slug = slug
        profile.save(update_fields=["slug"])
        used_slugs.add(slug)


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="publicprofile",
            name="slug",
            field=models.CharField(
                blank=True,
                max_length=100,
                null=True,
            ),
        ),
        migrations.RunPython(
            populate_public_profile_slugs,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="publicprofile",
            name="slug",
            field=models.SlugField(
                blank=True,
                max_length=100,
                unique=True,
            ),
        ),
    ]
