from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy

from core import models, tables, filters

from .base import BaseListView, FormViewMixin, BaseDeleteView
from .auth_mixins import CategoryPermissionMixin, BaseViewMixin
from django_select2 import forms as s2forms


class CategoryListView(CategoryPermissionMixin, BaseListView):
    model = models.EntryCategory
    table_class = tables.EntryCategoryTable
    filter_class = filters.EntryCategoryFilter
    get_stats = False
    table_pagination = False
    create_url = reverse_lazy('category-create')
    segment = 'categories'
    
    def get_queryset(self):
        # Filter categories by the user's company
        queryset = super().get_queryset()
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            return queryset.filter(company=self.request.user.profile.company)
        return queryset.none()


class CategoryCreateView(CategoryPermissionMixin, CreateView):
    model = models.EntryCategory
    template_name = 'generic/create.html'
    fields = ['category_title', 'finance_entry_type']
    segment = 'categories'
    success_url = reverse_lazy('category-list')

    widgets = {
        'finance_entry_type': s2forms.Select2Widget(choices=models.EntryType),
    }
    
    def get_initial(self):
        initial = super().get_initial()
        # If type parameter is provided in the URL, pre-select the entry type
        entry_type = self.request.GET.get('type')
        if entry_type and entry_type.isdigit():
            initial['finance_entry_type'] = int(entry_type)
        return initial
        
    def get_success_url(self):
        # If coming from expenses page, redirect back there
        referer = self.request.META.get('HTTP_REFERER', '')
        if 'expenses' in referer:
            return reverse_lazy('expense-list')
        return self.success_url
        
    def form_valid(self, form):
        # Set the company for the new category
        category = form.save(commit=False)
        if (not self.request.user.is_superuser and not self.request.user.is_staff and 
                hasattr(self.request.user, 'profile') and self.request.user.profile.company):
            category.company = self.request.user.profile.company
        elif hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            category.company = self.request.user.profile.company
        category.save()
        return super().form_valid(form)


class CategoryUpdateView(CategoryPermissionMixin, UpdateView):
    model = models.EntryCategory
    template_name = 'generic/detail.html'
    fields = ['category_title', 'finance_entry_type']
    segment = 'categories'

    widgets = {
        'finance_entry_type': s2forms.Select2Widget(choices=models.EntryType),
    }
    
    def get_queryset(self):
        # Ensure users can only update categories from their company
        queryset = super().get_queryset()
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            return queryset.filter(company=self.request.user.profile.company)
        return queryset.none()


class CategoryDeleteView(CategoryPermissionMixin, BaseDeleteView):
    model = models.EntryCategory
    success_url = reverse_lazy('category-list')
    
    def get_queryset(self):
        # Ensure users can only delete categories from their company
        queryset = super().get_queryset()
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            return queryset.filter(company=self.request.user.profile.company)
        return queryset.none()
