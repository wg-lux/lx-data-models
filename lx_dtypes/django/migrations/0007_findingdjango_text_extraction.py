from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("lx_dtypes_django", "0006_rename_video_hash_raw_video_hash")]

    operations = [
        migrations.AddField(
            model_name="findingdjango",
            name="text_extraction",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
