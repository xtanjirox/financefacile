import django_tables2 as tables
from . import models

ACTIONS_BUTTONS_TEMPLATE = """
<div class="btn-group">
    <a href="{{record.get_absolute_url}}" class="btn btn-sm shadow-sm" style="background: #fffde7; color: #f9a825; border-radius: 7px; font-weight: 500; border: none;" data-bs-toggle="tooltip" title="Edit">
        <i class="fas fa-edit"></i>
    </a>
    <a href="{{record.get_delete_url}}" class="btn btn-sm shadow-sm" style="background: #ffebee; color: #c62828; border-radius: 7px; font-weight: 500; border: none;" data-bs-toggle="tooltip" title="Delete">
        <i class="fas fa-trash"></i>
    </a>
</div>
"""

DEFAULT_TABLE_ATTRS = {
    "id": "datatables-orders",
    "class": "table table-responsive table-striped dataTable no-footer dtr-inline",
    "width": "100%",
    "aria - describedby": "datatables-orders_info",
    "style": "width: 100%;"
}


class ProductTable(tables.Table):
    actions = tables.TemplateColumn(ACTIONS_BUTTONS_TEMPLATE)

    class Meta:
        model = models.Product
        attrs = {"class": "table table-material"}
        fields = ('name', 'sku', 'quantity', 'unit_cost', 'selling_price', 'value_current', 'value_1_month', 'value_2_month', 'value_3_month', 'description', 'created_at')

class EntriesTable(tables.Table):
    actions = tables.TemplateColumn(ACTIONS_BUTTONS_TEMPLATE)

    class Meta:
        model = models.FinanceEntry
        attrs = DEFAULT_TABLE_ATTRS
        fields = ('entry_label', 'entry_category', 'finance_entry_type', 'entry_value', 'entry_date')


class ProductCategoryTable(tables.Table):
    actions = tables.TemplateColumn(ACTIONS_BUTTONS_TEMPLATE)

    class Meta:
        model = models.ProductCategory
        attrs = DEFAULT_TABLE_ATTRS
        fields = ('name', 'parent')

class EntryCategoryTable(tables.Table):
    actions = tables.TemplateColumn(ACTIONS_BUTTONS_TEMPLATE)

    class Meta:
        model = models.EntryCategory
        attrs = DEFAULT_TABLE_ATTRS
        fields = ('category_title', 'finance_entry_type')
