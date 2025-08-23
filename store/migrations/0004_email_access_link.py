from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_offline_delivery'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailAccessLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('token', models.CharField(max_length=64, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
            ],
        ),
    ]

