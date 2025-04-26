from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy

from core import models, tables, filters

from .base import BaseListView, FormViewMixin, BaseDeleteView
from django_select2 import forms as s2forms


class CategoryListView(BaseListView):
    model = models.EntryCategory
    table_class = tables.EntryCategoryTable
    filter_class = filters.EntryCategoryFilter
    get_stats = False
    table_pagination = False
    create_url = reverse_lazy('category-create')
    segment = 'categories'


class CategoryCreateView(CreateView, FormViewMixin):
    model = models.EntryCategory
    template_name = 'generic/create.html'
    fields = '__all__'
    segment = 'categories'
    success_url = reverse_lazy('category-list')

    widgets = {
        'finance_entry_type': s2forms.Select2Widget(choices=models.EntryType),
    }


class CategoryUpdateView(UpdateView, FormViewMixin):
    model = models.EntryCategory
    template_name = 'generic/detail.html'
    fields = '__all__'
    segment = 'categories'

    widgets = {
        'finance_entry_type': s2forms.Select2Widget(choices=models.EntryType),
    }


class CategoryDeleteView(BaseDeleteView):
    model = models.EntryCategory
    success_url = reverse_lazy('category-list')
