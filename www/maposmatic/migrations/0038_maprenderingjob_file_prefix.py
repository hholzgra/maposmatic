# created manually

import re

from django.db import migrations, models
from slugify import slugify

import www.settings

SPACE_REDUCE = re.compile(r"\s+")
NONASCII_REMOVE = re.compile(r"[^A-Za-z0-9]+")

BATCH_SIZE = 2000


def compute_files_prefix(job):
    """Generate file_prefix for already existing render requests 
    from rendering start time using the legacy format used so far
    """
    title = (job.maptitle or '').strip()
    if job.id <= www.settings.LAST_OLD_ID:
        title = SPACE_REDUCE.sub("-", title)
        title = NONASCII_REMOVE.sub("", title)
    else:
        title = slugify(title)

    if job.startofrendering_time is None:
        return "%06d_%s" % (job.id, title)

    ts = job.startofrendering_time
    return "%s/%06d_%s_%s" % (
        ts.strftime("%Y/%m/%d"),
        job.id,
        ts.strftime("%Y-%m-%d_%H-%M"),
        title
    )


def backfill_file_prefix(apps, schema_editor):
    MapRenderingJob = apps.get_model("maposmatic", "MapRenderingJob")

    last_id = 0
    while True:
        batch = list(
            MapRenderingJob.objects
            .filter(id__gt=last_id, file_prefix__isnull=True)
            .only("id", "maptitle", "startofrendering_time")
            .order_by("id")[:BATCH_SIZE]
        )
        if not batch:
            break

        for job in batch:
            job.file_prefix = compute_files_prefix(job)

        MapRenderingJob.objects.bulk_update(batch, ["file_prefix"])
        last_id = batch[-1].id


class Migration(migrations.Migration):

    # backfill runs over ~500k rows in batches; don't wrap it (and the
    # preceding AddField) in one giant transaction/lock
    atomic = False

    dependencies = [
        ('maposmatic', '0037_maprenderingjob_maposmatic__status_a5d174_idx'),
    ]

    operations = [
        migrations.AddField(
            model_name='maprenderingjob',
            name='file_prefix',
            field=models.CharField(max_length=512, null=True, blank=True),
        ),
        migrations.RunPython(backfill_file_prefix, migrations.RunPython.noop),
    ]
