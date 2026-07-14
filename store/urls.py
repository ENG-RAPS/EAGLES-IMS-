from django.urls import path
from . import views

app_name = 'store'   # <-- MUST be present

urlpatterns = [
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    

    # Transactions
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/add/', views.transaction_create, name='transaction_create'),
    path('transactions/<int:pk>/approve/', views.transaction_approve, name='transaction_approve'),


    # Categories
    
    path('categories/add/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edi  t/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('categories/', views.category_list, name='category_list'),


    # ... existing paths ...
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/edit/', views.supplier_edit, name='supplier_edit'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),
    

    # ===== REPORTS =====
    path('reports/products/', views.products_report, name='products_report'),
    path('reports/low-stock/', views.low_stock_report, name='low_stock_report'),
    path('reports/stock-movement/', views.stock_movement_report, name='stock_movement_report'),
    path('reports/stock-in/', views.stock_in_report, name='stock_in_report'),
    path('reports/stock-out/', views.stock_out_report, name='stock_out_report'),
    path('reports/department-consumption/', views.department_consumption_report, name='department_consumption_report'),
    path('reports/suppliers/', views.supplier_report, name='supplier_report'),
]