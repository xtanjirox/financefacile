from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Q
from core.models import Product, Invoice, ProductCategory

@require_GET
def live_search(request):
    query = request.GET.get('q', '').strip()
    results = {"products": [], "invoices": [], "categories": []}
    if query:
        products = Product.objects.filter(Q(name__icontains=query) | Q(sku__icontains=query))[:5]
        results["products"] = [
            {"id": p.id, "name": p.name, "sku": p.sku, "url": p.get_absolute_url()} for p in products
        ]
        invoices = Invoice.objects.filter(Q(id__icontains=query) | Q(created_at__icontains=query))[:5]
        results["invoices"] = [
            {"id": i.id, "date": i.created_at.strftime('%Y-%m-%d'), "url": i.get_absolute_url()} for i in invoices
        ]
        categories = ProductCategory.objects.filter(Q(name__icontains=query))[:5]
        results["categories"] = [
            {"id": c.id, "name": c.name, "url": "#"} for c in categories
        ]
    return JsonResponse(results)
