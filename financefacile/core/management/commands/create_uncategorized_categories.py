from django.core.management.base import BaseCommand
from accounts.models import Company
from core.models import ProductCategory, Product

class Command(BaseCommand):
    help = 'Creates an "Uncategorized" product category for each company and assigns uncategorized products to it'

    def handle(self, *args, **options):
        # Get all companies
        companies = Company.objects.all()
        self.stdout.write(f"Found {companies.count()} companies")
        
        categories_created = 0
        products_updated = 0
        
        # For each company, create an Uncategorized category if it doesn't exist
        for company in companies:
            # Check if the company already has an Uncategorized category
            uncategorized, created = ProductCategory.objects.get_or_create(
                company=company,
                name='Uncategorized',
                defaults={'parent': None}
            )
            
            if created:
                categories_created += 1
                self.stdout.write(f"Created 'Uncategorized' category for {company.name}")
            else:
                self.stdout.write(f"'Uncategorized' category already exists for {company.name}")
            
            # Find all products for this company that don't have a category
            uncategorized_products = Product.objects.filter(
                company=company,
                category__isnull=True
            )
            
            # Assign them to the Uncategorized category
            if uncategorized_products.exists():
                count = uncategorized_products.count()
                uncategorized_products.update(category=uncategorized)
                products_updated += count
                self.stdout.write(f"Assigned {count} products to 'Uncategorized' category for {company.name}")
        
        self.stdout.write(self.style.SUCCESS(
            f"Successfully created {categories_created} 'Uncategorized' categories and updated {products_updated} products"
        ))
