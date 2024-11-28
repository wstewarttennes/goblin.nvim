from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from datetime import timedelta
from celery.schedules import crontab


# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "goblin.settings")

app = Celery("goblin")

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.task_default_queue = "shared"

@app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request))


scheduled_tasks = {
    "ping_brain": {
        "task": "brain.tasks.ping_brain",
        "schedule": timedelta(minutes=1),
        "options": {"queue": "shared"},
    }
}

app.conf.beat_schedule = scheduled_tasks

