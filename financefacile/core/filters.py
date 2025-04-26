import django_filters
from . import models
from django_select2 import forms as s2forms
from django import forms


class FinanceEntryFilter(django_filters.FilterSet):
    entry_date = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(
            attrs={'placeholder': 'yyyy-mm-dd', "class": "form-control datepicker", "type": "date"})
    )

    entry_category = django_filters.ModelMultipleChoiceFilter(
        queryset=models.EntryCategory.objects.all(),
        widget=s2forms.Select2MultipleWidget(attrs={
            "data-live-search": "true",
            "class": "form-control selectpicker form-select"
        }
        ))

    class Meta:
        model = models.FinanceEntry
        fields = ['entry_date', 'entry_category']


class EntryCategoryFilter(django_filters.FilterSet):
    category_title = django_filters.ModelChoiceFilter(
        queryset=models.EntryCategory.objects.all(),
        widget=s2forms.ModelSelect2Widget(
            attrs={"class": "col-12"},
            model=models.EntryCategory,
            search_fields=['category_title__icontains']))

    class Meta:
        model = models.EntryCategory
        fields = ['category_title']
