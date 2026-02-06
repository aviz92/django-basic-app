from django.db import models


class FirstApp(models.Model):
    # Basic fields
    created_at = models.DateTimeField(verbose_name='Created at', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='Updated at', auto_now=True)
    name = models.CharField(verbose_name='Name', max_length=255, blank=False, unique=True)
    description = models.TextField(verbose_name='Description', null=True, blank=True)

    def __str__(self):
        return self.name
