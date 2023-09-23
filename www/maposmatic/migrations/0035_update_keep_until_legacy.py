# created manually

from django.db import migrations, models

def default_keep_until_for_old_rows(apps, schema_editor):
    files = apps.get_model("maposmatic", "uploadfile")
    files.objects.filter(keep_until__isnull = True, deleted_on__isnull = True).update(keep_until = '2999-12-30')

class Migration(migrations.Migration):

    dependencies = [
        ('maposmatic', '0034_uploadfile_created_on_uploadfile_deleted_on'),
    ]

    operations = [
        migrations.RunPython(default_keep_until_for_old_rows),
    ]
