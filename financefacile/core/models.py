from django.db import models
from django.contrib.auth.models import User

from django.utils import timezone
from django.urls import reverse_lazy
from datetime import datetime


class EntryType(models.IntegerChoices):
    CHARGE = 1, 'DEPENSE'
    REVENUE = 2, 'REVENUE'


class EntryCategory(models.Model):
    category_title = models.CharField(max_length=50)
    finance_entry_type = models.IntegerField(choices=EntryType.choices)

    class Meta:
        db_table = 'entry_category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.category_title

    def get_absolute_url(self):
        return reverse_lazy('category-update', kwargs={'pk': self.pk})

    def get_delete_url(self):
        return reverse_lazy('category-delete', kwargs={"pk": self.pk})


class FinanceEntry(models.Model):
    finance_entry_type = models.IntegerField(choices=EntryType.choices)
    entry_category = models.ForeignKey(EntryCategory, on_delete=models.DO_NOTHING)
    entry_value = models.FloatField(default=0)
    entry_label = models.CharField(max_length=20)
    entry_date = models.DateField(default=timezone.now())

    class Meta:
        db_table = 'finance_entries'
        verbose_name_plural = 'entries'

    def __str__(self):
        return str(self.pk) + str(self.entry_label)

    def get_absolute_url(self):
        return reverse_lazy('entry-update', kwargs={'pk': self.pk})

    def get_delete_url(self):
        return reverse_lazy('entry-delete', kwargs={"pk": self.pk})

    @property
    def month_year(self):
        return datetime(self.entry_date.year, self.entry_date.month, 1).strftime("%B%Y")


