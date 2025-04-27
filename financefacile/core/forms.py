from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout

from core import models
from django_select2 import forms as s2forms

class InvoiceForm(forms.ModelForm):
    invoice_total = forms.DecimalField(
        max_digits=12, decimal_places=2, required=False,
        label="Invoice Total",
        widget=forms.NumberInput(attrs={"class": "form-control form-control-lg invoice-grand-total", "placeholder": "Total invoice amount"})
    )
    class Meta:
        model = models.Invoice
        fields = []  # Add fields if you extend Invoice (e.g. customer)

class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = models.InvoiceItem
        fields = ['product', 'quantity', 'selling_price']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = models.Product.objects.all()

from django.forms import inlineformset_factory
InvoiceItemFormSet = inlineformset_factory(
    models.Invoice, models.InvoiceItem, form=InvoiceItemForm,
    fields=['product', 'quantity', 'selling_price'], extra=1, can_delete=True
)

class ProductCategoryWidget(s2forms.ModelSelect2Widget):
    model = models.ProductCategory
    search_fields = ['name__icontains']

class ProductForm(forms.ModelForm):
    debug_marker = "THIS IS THE REAL ProductForm"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        import sys
        print("ProductForm INIT DEBUG:", file=sys.stderr)
        print("  Meta.model:", getattr(self._meta, 'model', None), file=sys.stderr)
        print("  Meta.fields:", getattr(self._meta, 'fields', None), file=sys.stderr)
        print("  Fields:", list(self.fields.keys()), file=sys.stderr)

    class Meta:
        model = models.Product
        fields = '__all__'
        widgets = {
            'category': forms.Select(attrs={"class": "form-control", "style": "width: 100%;"}),
            'name': forms.TextInput(attrs={"class": "form-control", "style": "width: 100%;"}),
            'sku': forms.TextInput(attrs={"class": "form-control", "style": "width: 100%;"}),
            'quantity': forms.NumberInput(attrs={"class": "form-control", "style": "width: 100%;"}),
            'unit_cost': forms.NumberInput(attrs={"class": "form-control", "style": "width: 100%;"}),
            'selling_price': forms.NumberInput(attrs={"class": "form-control", "style": "width: 100%;"}),
            'value_current': forms.NumberInput(attrs={"class": "form-control", "style": "width: 100%;"}),
            'value_1_month': forms.NumberInput(attrs={"class": "form-control", "style": "width: 100%;"}),
            'value_2_month': forms.NumberInput(attrs={"class": "form-control", "style": "width: 100%;"}),
            'value_3_month': forms.NumberInput(attrs={"class": "form-control", "style": "width: 100%;"}),
            'description': forms.Textarea(attrs={"class": "form-control", "rows": 4, "style": "width: 100%;"}),
        }

class FilterForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.form_tag = False
        fields = (Div(field, css_class='col-md-4') for field in args[0].fields.keys())
        self.helper.layout = Layout(
            Div(
                *fields,
                css_class='row'
            )
        )

