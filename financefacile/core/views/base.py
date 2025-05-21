from django_tables2 import SingleTableView
from django.forms import modelform_factory
from django.views import generic
from django.db.models import Q

from core import forms
from .auth_mixins import BaseViewMixin


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
