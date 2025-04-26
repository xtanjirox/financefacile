from django.contrib import admin
from . import models

admin.site.register(models.FinanceEntry)
admin.site.register(models.EntryCategory)
