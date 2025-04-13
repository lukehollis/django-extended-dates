from django.db import models
from django_extended_dates.fields import ExtendedDateTimeField

class TestModel(models.Model):
    name = models.CharField(max_length=50)
    timestamp = ExtendedDateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name
