from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('cameras', '0001_initial')]

    operations = [
        migrations.AddField(
            model_name='camera',
            name='location_name',
            field=models.CharField(blank=True, max_length=120),
        ),
    ]
