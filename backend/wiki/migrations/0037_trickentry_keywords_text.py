from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wiki", "0036_trickentrylike"),
    ]

    operations = [
        migrations.AddField(
            model_name="trickentry",
            name="keywords_text",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
