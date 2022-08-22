from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('maposmatic', '0025_maprenderingjob_indexer'),
    ]

    operations = [
        migrations.RunSQL("UPDATE maposmatic_maprenderingjob j SET indexer = 'poi' FROM maposmatic_uploadfile_job uj, maposmatic_uploadfile u WHERE j.id = uj.maprenderingjob_id AND uj.uploadfile_id = u.id AND u.file_type = 'poi'"),
    ]
