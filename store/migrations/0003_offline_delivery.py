from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0002_game_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='instructions',
            field=models.TextField(blank=True, help_text='Optional instructions shown on delivery page for offline accounts'),
        ),
        migrations.AddField(
            model_name='game',
            name='rotation_index',
            field=models.PositiveIntegerField(default=0, help_text='Round-robin pointer for offline account credentials'),
        ),
        migrations.CreateModel(
            name='GameCredential',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=255)),
                ('password', models.CharField(max_length=255)),
                ('notes', models.CharField(blank=True, max_length=255)),
                ('game', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='credentials', to='store.game')),
            ],
        ),
        migrations.CreateModel(
            name='OfflineCredentialAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=255)),
                ('password', models.CharField(max_length=255)),
                ('notes', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('game', models.ForeignKey(on_delete=models.deletion.CASCADE, to='store.game')),
                ('order', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='offline_assignments', to='store.order')),
            ],
        ),
        migrations.CreateModel(
            name='DeliveryLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=64, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('order', models.OneToOneField(on_delete=models.deletion.CASCADE, related_name='delivery_link', to='store.order')),
            ],
        ),
    ]

