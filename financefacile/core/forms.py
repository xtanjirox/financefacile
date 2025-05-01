from django.forms import inlineformset_factory
from django import forms
from django.utils import timezone

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout, Submit, Button, HTML

from core import models
from django_select2 import forms as s2forms


class CategoryMultiSelectWidget(s2forms.Select2MultipleWidget):
    def build_attrs(self, *args, **kwargs):
        attrs = super().build_attrs(*args, **kwargs)
        attrs.update({
            'data-placeholder': 'Select categories...',
            'data-minimum-input-length': 0,
            'class': 'form-control select2-widget',
            'style': 'width: 100%;',
            'data-allow-clear': 'true',
            'data-dropdown-css-class': 'select2-dropdown-open',
            'data-close-on-select': 'false'
        })
        return attrs


class DateRangeFilterForm(forms.Form):
    start_date = forms.DateField(
        label='Start Date',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        label='End Date',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    category_name = forms.MultipleChoiceField(
        label='Categories',
        required=False,
        widget=CategoryMultiSelectWidget()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically populate category choices
        categories = models.ExpenseCategory.objects.all().order_by('name')
        self.fields['category_name'].choices = [
            ('', '---------')] + [(cat.name, cat.name) for cat in categories]

        # Setup crispy form helper
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'form-inline'
        self.helper.layout = Layout(
            Div(
                Div('start_date', css_class='col-md-3'),
                Div('end_date', css_class='col-md-3'),
                Div('category_name', css_class='col-md-3'),
                Div(
                    Submit('submit', 'Filter', css_class='btn-primary me-2'),
                    HTML('<a href="?" class="btn btn-secondary">Reset</a>'),
                    css_class='col-md-3 d-flex align-items-end'
                ),
                css_class='row'
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError('End date must be after start date')

        return cleaned_data


class DateRangeCategoryFilterForm(forms.Form):
    start_date = forms.DateField(
        label='Start Date',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        label='End Date',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Setup crispy form helper
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'form-inline'
        self.helper.layout = Layout(
            Div(
                Div('start_date', css_class='col-md-3'),
                Div('end_date', css_class='col-md-3'),
                Div(
                    Submit('submit', 'Filter', css_class='btn-primary me-2'),
                    HTML('<a href="?" class="btn btn-secondary">Reset</a>'),
                    css_class='col-md-3 d-flex align-items-end'
                ),
                css_class='row'
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError('End date must be after start date')

        return cleaned_data

class InvoiceForm(forms.ModelForm):
    invoice_total = forms.DecimalField(
        max_digits=12, decimal_places=2, required=False,
        label="Invoice Total",
        widget=forms.NumberInput(attrs={
                                 "class": "form-control form-control-lg invoice-grand-total", "placeholder": "Total invoice amount"})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get default TVA rate from site settings
        site_settings = models.SiteSettings.get_settings()
        
        # Set initial values for TVA rate and include_stamp_fee
        if not self.instance.pk:  # New invoice
            self.fields['tva_rate'].initial = site_settings.default_tva_rate
            self.fields['include_stamp_fee'].initial = True
        
        # Add help text with current stamp fee amount
        self.fields['include_stamp_fee'].help_text = f"Include stamp fee of {site_settings.stamp_fee} in this invoice"

    class Meta:
        model = models.Invoice
        fields = ['tva_rate', 'include_stamp_fee']


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = models.InvoiceItem
        fields = ['product', 'quantity', 'selling_price']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = models.Product.objects.all()


InvoiceItemFormSet = inlineformset_factory(
    models.Invoice, models.InvoiceItem, form=InvoiceItemForm,
    fields=['product', 'quantity', 'selling_price'], extra=1, can_delete=True
)


class ProductCategoryWidget(s2forms.ModelSelect2Widget):
    model = models.ProductCategory
    search_fields = ['name__icontains']

    def build_attrs(self, *args, **kwargs):
        attrs = super().build_attrs(*args, **kwargs)
        attrs.update({
            'data-placeholder': 'Select a category...',
            'data-minimum-input-length': 0,
            'class': 'form-control select2-widget',
            'style': 'width: 100%;'
        })
        return attrs


class ProductForm(forms.ModelForm):
    debug_marker = "THIS IS THE REAL ProductForm"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        import sys
        print("ProductForm INIT DEBUG:", file=sys.stderr)
        print("  Meta.model:", getattr(
            self._meta, 'model', None), file=sys.stderr)
        print("  Meta.fields:", getattr(
            self._meta, 'fields', None), file=sys.stderr)
        print("  Fields:", list(self.fields.keys()), file=sys.stderr)

        # Ensure the category queryset is populated
        if 'category' in self.fields:
            self.fields['category'].queryset = models.ProductCategory.objects.all(
            ).order_by('name')

    class Meta:
        model = models.Product
        fields = '__all__'
        widgets = {
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


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = models.Expense
        fields = ['category', 'date', 'amount', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].input_formats = ['%Y-%m-%d']
        self.fields['date'].localize = False
        if self.instance and self.instance.pk and self.instance.date:
            self.fields['date'].initial = self.instance.date.strftime(
                '%Y-%m-%d')
        # Fix initial date if provided in DD/MM/YYYY
        if 'initial' in kwargs and 'date' in kwargs['initial']:
            d = kwargs['initial']['date']
            if isinstance(d, str) and '/' in d:
                try:
                    day, month, year = d.split('/')
                    self.fields['date'].initial = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except Exception:
                    pass
        # If form is bound (POST), forcibly correct the value
        if self.is_bound:
            data = self.data.copy()
            val = data.get(self.add_prefix('date'))
            if val and '/' in val:
                try:
                    day, month, year = val.split('/')
                    data[self.add_prefix(
                        'date')] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    self.data = data
                except Exception:
                    pass


class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = models.ExpenseCategory
        fields = ['name']


class FilterForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.form_tag = False
        fields = (Div(field, css_class='col-md-4')
                  for field in args[0].fields.keys())
        self.helper.layout = Layout(
            Div(
                *fields,
                css_class='row'
            )
        )
