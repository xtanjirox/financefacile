from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Q
from django.urls import reverse_lazy
from core.models import Product, Invoice, ProductCategory
import logging

logger = logging.getLogger(__name__)

@require_GET
def live_search(request):
    query = request.GET.get('q', '').strip()
    results = {"products": [], "invoices": [], "categories": []}
    
    # Get the user's company if available
    user = request.user
    company = None
    if hasattr(user, 'profile') and user.profile and user.profile.company:
        company = user.profile.company
    
    logger.info(f"Live search query: '{query}' from user: {user.username}, company: {company}")
    
    if query:
        try:
            # Filter products by company and query
            product_filter = Q(name__icontains=query) | Q(sku__icontains=query)
            if company and (not user.is_superuser and not user.is_staff):
                product_filter &= Q(company=company)
            
            products = Product.objects.filter(product_filter)[:5]
            results["products"] = [
                {"id": p.id, "name": p.name, "sku": p.sku or "", "url": reverse_lazy('product-detail', kwargs={'pk': p.pk})} 
                for p in products
            ]
            logger.info(f"Found {len(results['products'])} products matching '{query}'")
            
            # Filter invoices by company and query
            invoice_filter = Q(id__icontains=query) | Q(created_at__icontains=query)
            if company and (not user.is_superuser and not user.is_staff):
                invoice_filter &= Q(company=company)
                
            invoices = Invoice.objects.filter(invoice_filter)[:5]
            results["invoices"] = [
                {"id": i.id, "date": i.created_at.strftime('%Y-%m-%d'), "url": reverse_lazy('invoice-detail', kwargs={'pk': i.pk})} 
                for i in invoices
            ]
            logger.info(f"Found {len(results['invoices'])} invoices matching '{query}'")
            
            # Filter categories by company and query
            category_filter = Q(name__icontains=query)
            if company and (not user.is_superuser and not user.is_staff):
                category_filter &= Q(company=company)
                
            categories = ProductCategory.objects.filter(category_filter)[:5]
            results["categories"] = [
                {"id": c.id, "name": c.name, "url": reverse_lazy('category-list')} 
                for c in categories
            ]
            logger.info(f"Found {len(results['categories'])} categories matching '{query}'")
            
        except Exception as e:
            logger.error(f"Error in live search: {str(e)}")
            # Return empty results on error
            results = {"products": [], "invoices": [], "categories": []}
    
    return JsonResponse(results)
