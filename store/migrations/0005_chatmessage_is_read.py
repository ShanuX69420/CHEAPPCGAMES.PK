from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('store', '0004_chatmessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatmessage',
            name='is_read',
            field=models.BooleanField(default=False, help_text='Marked read by staff when viewed'),
        ),
    ]

