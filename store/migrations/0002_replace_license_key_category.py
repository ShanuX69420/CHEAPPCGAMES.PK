from django.db import migrations


def forwards(apps, schema_editor):
    Game = apps.get_model('store', 'Game')
    Game.objects.filter(category='license-key').update(category='online-account')


def backwards(apps, schema_editor):
    Game = apps.get_model('store', 'Game')
    # If rolling back, map online-account back to license-key where appropriate.
    Game.objects.filter(category='online-account').update(category='license-key')


class Migration(migrations.Migration):
    dependencies = [
        ('store', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]

