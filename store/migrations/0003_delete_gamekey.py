from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('store', '0002_replace_license_key_category'),
    ]

    operations = [
        migrations.DeleteModel(
            name='GameKey',
        ),
    ]

