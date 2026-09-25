from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("lx_dtypes_django", "0005_videofiledjango")]

    operations = [
        migrations.RenameField(
            model_name="videofiledjango",
            old_name="video_hash",
            new_name="raw_video_hash",
        ),
    ]
