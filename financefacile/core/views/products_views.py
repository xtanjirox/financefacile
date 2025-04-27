from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from core import models, tables
from .base import BaseListView, FormViewMixin, BaseDeleteView
import core.forms
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.db.models import Sum

from core import tables

from core.models import InvoiceItem

class ProductCategoryListView(BaseListView):
    model = models.ProductCategory
    table_class = tables.ProductCategoryTable
    filter_class = None
    get_stats = False
    table_pagination = {'per_page': 10}
    create_url = reverse_lazy('category-create')
    segment = 'categories'
    detail = True

class ProductCategoryCreateView(CreateView, FormViewMixin):
    model = models.ProductCategory
    template_name = 'generic/create.html'
    fields = '__all__'
    segment = 'categories'
    success_url = reverse_lazy('category-list')

class ProductCategoryUpdateView(UpdateView, FormViewMixin):
    model = models.ProductCategory
    template_name = 'generic/detail.html'
    fields = '__all__'
    segment = 'categories'
    success_url = reverse_lazy('category-list')

class ProductCategoryDeleteView(BaseDeleteView):
    model = models.ProductCategory
    success_url = reverse_lazy('category-list')

class ProductListView(BaseListView):
    model = models.Product
    table_class = tables.ProductTable
    filter_class = None  # You can define a filter if needed
    get_stats = False
    table_pagination = {'per_page': 10}
    create_url = reverse_lazy('product-create')
    segment = 'products'
    detail = True

from django_select2 import forms as s2forms

import core.forms

class ProductCreateView(CreateView):
    def dispatch(self, *args, **kwargs):
        import sys
        print("DISPATCH ProductCreateView", file=sys.stderr)
        return super().dispatch(*args, **kwargs)

    model = models.Product
    form_class = core.forms.ProductForm
    template_name = 'generic/create.html'
    segment = 'products'
    success_url = reverse_lazy('product-list')



class ProductUpdateView(UpdateView):
    model = models.Product
    form_class = core.forms.ProductForm
    template_name = 'generic/detail.html'
    segment = 'products'
    success_url = reverse_lazy('product-list')


class ProductDeleteView(BaseDeleteView):
    model = models.Product
    success_url = reverse_lazy('product-list')

class ProductDetailView(DetailView):
    model = models.Product
    template_name = 'products/product_detail.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Find all InvoiceItems for this product, prefetch related invoice
        context['invoices'] = InvoiceItem.objects.filter(product=self.object).select_related('invoice')
        return context


from django.views import View

from django.views.generic.edit import CreateView
from django.forms import modelformset_factory

class InvoiceCreateView(CreateView):
    model = models.Invoice
    form_class = core.forms.InvoiceForm
    template_name = 'invoices/invoice_form.html'
    success_url = None  # Will be set in form_valid

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = core.forms.InvoiceItemFormSet(self.request.POST)
        else:
            context['formset'] = core.forms.InvoiceItemFormSet()
        # Add all products for JS price autofill
        context['products'] = models.Product.objects.all()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            self.object = form.save(commit=False)
            # Save custom total from form
            invoice_total = form.cleaned_data.get('invoice_total')
            if invoice_total is not None:
                self.object.custom_total = invoice_total
            self.object.save()
            formset.instance = self.object
            formset.save()
            # Update inventory for each item
            for item in self.object.items.all():
                product = item.product
                product.quantity = max(0, product.quantity - item.quantity)
                product.save()
            return redirect(self.object.get_absolute_url())
        else:
            return self.form_invalid(form)

from django.views.generic import ListView
class InvoiceListView(ListView):
    model = models.Invoice
    template_name = 'invoices/invoice_list.html'
    context_object_name = 'invoices'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import InvoiceItem
        from django.db.models import Sum
        # 1. Total items sold
        total_items_sold = InvoiceItem.objects.aggregate(total=Sum('quantity'))['total'] or 0
        # 2. Total inventory sold value (sum of quantity * product.unit_cost)
        total_inventory_sold_value = sum(
            item.quantity * item.product.unit_cost for item in InvoiceItem.objects.select_related('product').all()
        )
        # 3. Total price of invoices (sum of all invoice totals)
        total_invoice_price = models.Invoice.objects.aggregate(total=Sum('items__total_price'))['total'] or 0
        context.update({
            'total_items_sold': total_items_sold,
            'total_inventory_sold_value': total_inventory_sold_value,
            'total_invoice_price': total_invoice_price,
        })
        return context

from django.views.generic import DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
class InvoiceUpdateView(UpdateView):
    model = models.Invoice
    form_class = core.forms.InvoiceForm
    template_name = 'invoices/invoice_form.html'
    success_url = reverse_lazy('invoice-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = core.forms.InvoiceItemFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = core.forms.InvoiceItemFormSet(instance=self.object)
        # Add all products for JS price autofill
        context['products'] = models.Product.objects.all()
        return context

    def form_valid(self, form):
        import logging
        from django.db import transaction
        logger = logging.getLogger(__name__)
        context = self.get_context_data()
        formset = context['formset']
        logger.debug('InvoiceUpdateView.form_valid called')
        logger.debug(f'Form valid: {form.is_valid()}')
        logger.debug(f'Formset valid: {formset.is_valid()}')
        logger.debug(f'POST data: {self.request.POST}')
        with transaction.atomic():
            if formset.is_valid():
                # Save invoice object without committing to DB
                obj = form.save(commit=False)
                # Save custom total from form
                invoice_total = form.cleaned_data.get('invoice_total')
                if invoice_total is not None:
                    obj.custom_total = invoice_total
                obj.save()
                formset.instance = obj

                # Restore inventory for all previous items
                previous_items = list(obj.items.all())
                logger.debug(f'Restoring inventory for previous items: {previous_items}')
                for item in previous_items:
                    product = item.product
                    logger.debug(f'Before restore: {product.name} quantity={product.quantity}, restoring {item.quantity}')
                    product.quantity += item.quantity
                    product.save()
                    logger.debug(f'After restore: {product.name} quantity={product.quantity}')

                # Save formset (this will handle deletions)
                formset.save()
                logger.debug(f'Formset saved for invoice {obj.pk}')

                # Subtract inventory for all new items
                logger.debug(f'Adjusting inventory for new items: {list(obj.items.all())}')
                for item in obj.items.all():
                    product = item.product
                    logger.debug(f'Before subtract: {product.name} quantity={product.quantity}, subtracting {item.quantity}')
                    product.quantity = max(0, product.quantity - item.quantity)
                    product.save()
                    logger.debug(f'After subtract: {product.name} quantity={product.quantity}')
                logger.info(f'Invoice {obj.pk} updated successfully.')
                return redirect(self.get_success_url())
            else:
                logger.error('Formset invalid during invoice update')
                logger.error(f'Formset errors: {formset.errors}')
                logger.error(f'Non-form errors: {formset.non_form_errors()}')
                return self.form_invalid(form)


class InvoiceDeleteView(DeleteView):
    model = models.Invoice
    template_name = 'invoices/invoice_confirm_delete.html'
    success_url = reverse_lazy('invoice-list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Restore inventory for all items in the invoice
        for item in self.object.items.all():
            product = item.product
            product.quantity += item.quantity
            product.save()
        return super().delete(request, *args, **kwargs)


class InvoiceDetailView(DetailView):
    model = models.Invoice
    template_name = 'invoices/invoice_detail.html'
    context_object_name = 'invoice'
