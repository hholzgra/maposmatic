from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('maposmatic', '0026_maprenderingjob_indexer'),
    ]

    operations = [
        migrations.RunSQL("UPDATE maposmatic_maprenderingjob SET indexer = 'StreetIndex' WHERE indexer = 'Street'"),
        migrations.RunSQL("UPDATE maposmatic_maprenderingjob SET indexer = 'PoiIndex'    WHERE indexer = 'Poi'"),
    ]
