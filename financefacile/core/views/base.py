from django_tables2 import SingleTableView
from django.forms import modelform_factory
from django.views import generic
from django.db.models import F, Q, Sum
from django.contrib.auth.mixins import LoginRequiredMixin

from core import forms, models
from .auth_mixins import BaseViewMixin

import random
import json


def generate_color(n):
    chars = '0123456789ABCDEF'
    return ['#' + ''.join(random.sample(chars, 6)) for i in range(n)]


class BaseListView(BaseViewMixin, SingleTableView):
    template_name = "generic/list.html"
    segment = None
    filter_class = None
    show_only_filtered = None
    filter = None
    entry_type = None
    create_url = None
    get_stats = None
    detail = None

    def get_queryset(self):
        if self.filter_class:
            self.filter = self.filter_class(self.request.GET, queryset=super().get_queryset())
            if self.show_only_filtered and not self.request.GET:
                return self.model.objects.none()
            if self.entry_type:
                q_entry_type = Q(finance_entry_type=self.entry_type)
            else:
                q_entry_type = Q()
            return self.filter.qs.filter(q_entry_type)
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.filter_class:
            form = forms.FilterForm(self.filter.form)
            context.update({
                'filter': self.filter,
                'helper': form.helper
            })
        if self.get_stats:
            qs = context.get('object_list')
            total_charge = sum(
                qs.filter(finance_entry_type=models.EntryType.CHARGE).values_list('entry_value', flat=True))
            total_revenue = sum(
                qs.filter(finance_entry_type=models.EntryType.REVENUE).values_list('entry_value', flat=True))

            total_charge_per_category = qs.filter(finance_entry_type=models.EntryType.CHARGE).values(
                'entry_category'
            ).annotate(total_sum=Sum('entry_value')).annotate(category_name=F('entry_category__category_title'))
            total_charge_per_category = total_charge_per_category.values('category_name', 'total_sum')

            stats_charge_pie = {
                "labels": list(total_charge_per_category.values_list('category_name', flat=True)),
                "datasets": [{
                    "data": list(total_charge_per_category.values_list('total_sum', flat=True)),
                    "backgroundColor": generate_color(len(total_charge_per_category)),
                    "borderWidth": 5
                }]
            }

            context.update({
                'total_charge': total_charge,
                'total_revenue': total_revenue,
                'total_benefice': total_revenue - total_charge,
                'ls_stats': [total_revenue, total_charge],
                'data': json.dumps(stats_charge_pie),
                'pie_charge': total_charge_per_category
            })

        context.update({
            'segment': self.segment,
            'create_url': self.create_url,
            'detail': self.detail
        })
        return context


class FormViewMixin(BaseViewMixin, generic.FormView):
    model = None
    fields = []
    attrs = {}
    widgets = {}
    exclude = None
    readonly_fields = []
    segment = None

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = modelform_factory(
                self.model, fields=self.fields, exclude=self.exclude, widgets=self.widgets
            )
        form = super().get_form(form_class=form_class)
        form.helper = forms.FormHelper()
        form.helper.form_tag = False
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'segment': self.segment
        })
        return context


class BaseDeleteView(BaseViewMixin, generic.DeleteView):
    skip_confirmation = True

    def get(self, request, *args, **kwargs):
        if self.skip_confirmation:
            return self.delete(request, *args, **kwargs)
        return super().get(request, *args, **kwargs)
