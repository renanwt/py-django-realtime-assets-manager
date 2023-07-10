from django.db import models
import uuid
from django.utils import timezone


class QuerySet(models.QuerySet):
    def presente(self):
        return self.filter(presente=True)


class BaseModel(models.Model):
    id = models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    created = models.DateTimeField(default=timezone.now, blank=True)
    modified = models.DateTimeField(default=timezone.now, blank=True)
    presente = models.BooleanField(default=True)

    objects = QuerySet.as_manager()

    class Meta:
        abstract = True
