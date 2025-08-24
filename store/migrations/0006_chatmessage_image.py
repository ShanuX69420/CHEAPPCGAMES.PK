from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [
        ('store', '0005_chatmessage_is_read'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatmessage',
            name='message',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='image',
            field=models.FileField(blank=True, null=True, upload_to='chat_uploads/%Y/%m/%d', validators=[django.core.validators.FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif', 'webp'])]),
        ),
    ]

