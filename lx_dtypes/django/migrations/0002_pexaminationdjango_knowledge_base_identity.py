from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("lx_dtypes_django", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="pexaminationdjango",
            name="knowledge_base_module",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="pexaminationdjango",
            name="knowledge_base_version",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
