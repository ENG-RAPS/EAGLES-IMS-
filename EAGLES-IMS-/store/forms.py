# store/forms.py
from django import forms
from .models import Product, StockTransaction, Category, Supplier

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'item_code', 'unit', 
                  'quantity', 'minimum_stock_level', 'supplier', 'storage_location']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class TransactionForm(forms.ModelForm):
    class Meta:
        model = StockTransaction
        fields = ['product', 'transaction_type', 'quantity', 'unit_price', 
                  'supplier', 'department', 'remarks']
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['company_name', 'contact_person', 'phone', 'email', 'address']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }