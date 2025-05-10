from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy

from core import models, tables, filters

from .base import BaseListView, FormViewMixin, BaseDeleteView
from .auth_mixins import FinanceEntryPermissionMixin, BaseViewMixin
from django_select2 import forms as s2forms


class FianceEntryListView(FinanceEntryPermissionMixin, BaseListView):
    model = models.FinanceEntry
    table_class = tables.EntriesTable
    filter_class = filters.FinanceEntryFilter
    get_stats = True
    table_pagination = False
    create_url = reverse_lazy('entry-create')
    segment = 'entries'
    detail = True
    
    def get_queryset(self):
        # Filter entries by the user's company
        queryset = super().get_queryset()
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            return queryset.filter(company=self.request.user.profile.company)
        return queryset.none()


class FianceEntryCreateView(FinanceEntryPermissionMixin, CreateView):
    model = models.FinanceEntry
    template_name = 'generic/create.html'
    fields = ['finance_entry_type', 'entry_category', 'entry_date', 'amount', 'description']
    segment = 'entries'
    success_url = reverse_lazy('entry-list')

    widgets = {
        'finance_entry_type': s2forms.Select2Widget(choices=models.EntryType),
        'entry_category': s2forms.ModelSelect2Widget(
            model=models.EntryCategory,
            search_fields=['category_title__icontains'],
            attr={"id": "js-example-basic-single"}
        )
    }
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filter category choices to only show categories from the user's company
        if not self.request.user.is_superuser and not self.request.user.is_staff:
            if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
                form.fields['entry_category'].queryset = models.EntryCategory.objects.filter(
                    company=self.request.user.profile.company
                )
        return form
    
    def form_valid(self, form):
        # Set the company and created_by for the new entry
        entry = form.save(commit=False)
        if (not self.request.user.is_superuser and not self.request.user.is_staff and 
                hasattr(self.request.user, 'profile') and self.request.user.profile.company):
            entry.company = self.request.user.profile.company
        elif hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            entry.company = self.request.user.profile.company
        
        entry.created_by = self.request.user
        entry.save()
        return super().form_valid(form)


class FianceEntryUpdateView(FinanceEntryPermissionMixin, UpdateView):
    model = models.FinanceEntry
    template_name = 'generic/detail.html'
    fields = ['finance_entry_type', 'entry_category', 'entry_date', 'amount', 'description']
    segment = 'entries'
    success_url = reverse_lazy('entry-list')

    widgets = {
        'finance_entry_type': s2forms.Select2Widget(choices=models.EntryType),
        'entry_category': s2forms.ModelSelect2Widget(
            model=models.EntryCategory,
            search_fields=['category_title__icontains'],
            attr={"id": "js-example-basic-single"}
        )
    }
    
    def get_queryset(self):
        # Ensure users can only update entries from their company
        queryset = super().get_queryset()
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            return queryset.filter(company=self.request.user.profile.company)
        return queryset.none()
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filter category choices to only show categories from the user's company
        if not self.request.user.is_superuser and not self.request.user.is_staff:
            if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
                form.fields['entry_category'].queryset = models.EntryCategory.objects.filter(
                    company=self.request.user.profile.company
                )
        return form


class FianceEntryDeleteView(FinanceEntryPermissionMixin, BaseDeleteView):
    model = models.FinanceEntry
    success_url = reverse_lazy('entry-list')
    
    def get_queryset(self):
        # Ensure users can only delete entries from their company
        queryset = super().get_queryset()
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            return queryset.filter(company=self.request.user.profile.company)
        return queryset.none()


class ChargeListView(FinanceEntryPermissionMixin, BaseListView):
    model = models.FinanceEntry
    table_class = tables.EntriesTable
    filter_class = filters.FinanceEntryFilter
    get_stats = True
    table_pagination = False
    create_url = False
    entry_type = models.EntryType.CHARGE
    segment = 'entries'
    
    def get_queryset(self):
        # Filter charges by the user's company
        queryset = super().get_queryset()
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            return queryset.filter(company=self.request.user.profile.company)
        return queryset.none()


class RevenueListView(FinanceEntryPermissionMixin, BaseListView):
    model = models.FinanceEntry
    table_class = tables.EntriesTable
    filter_class = filters.FinanceEntryFilter
    get_stats = True
    table_pagination = False
    create_url = False
    entry_type = models.EntryType.REVENUE
    segment = 'entries'
    
    def get_queryset(self):
        # Filter revenues by the user's company
        queryset = super().get_queryset()
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            return queryset.filter(company=self.request.user.profile.company)
        return queryset.none()
