from django.urls import path
from . import views

app_name = 'biomed'

urlpatterns = [
    # Equipment
    path('equipment/', views.equipment_list, name='equipment_list'),
    path('equipment/add/', views.equipment_create, name='equipment_create'),
    path('equipment/<int:pk>/', views.equipment_detail, name='equipment_detail'),
    path('equipment/<int:pk>/edit/', views.equipment_edit, name='equipment_edit'),
    path('equipment/<int:pk>/delete/', views.equipment_delete, name='equipment_delete'),


    # PPM
    path('ppm/', views.ppm_list, name='ppm_list'),
    path('ppm/add/', views.ppm_create, name='ppm_create'),
    path('ppm/<int:pk>/', views.ppm_detail, name='ppm_detail'),
    path('ppm/<int:pk>/edit/', views.ppm_edit, name='ppm_edit'),
    path('ppm/<int:pk>/delete/', views.ppm_delete, name='ppm_delete'),


    # StockTake
    path('stocktake/', views.stocktake_list, name='stocktake_list'),
    path('stocktake/add/', views.stocktake_create, name='stocktake_create'),
    path('stocktake/<int:pk>/', views.stocktake_detail, name='stocktake_detail'),
    path('stocktake/<int:pk>/edit/', views.stocktake_edit, name='stocktake_edit'),
    path('stocktake/<int:pk>/delete/', views.stocktake_delete, name='stocktake_delete'),


    # Equipment Transfers
path('transfers/', views.transfer_list, name='transfer_list'),
path('transfers/add/', views.transfer_create, name='transfer_create'),
path('transfers/<int:pk>/', views.transfer_detail, name='transfer_detail'),
path('transfers/<int:pk>/approve/', views.transfer_approve, name='transfer_approve'),
path('transfers/<int:pk>/reject/', views.transfer_reject, name='transfer_reject'),



# biomed Categories
path('categories/', views.category_list, name='category_list'),
path('categories/add/', views.category_create, name='category_create'),
path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),


    # ===== REPORTS =====
path('reports/equipment/', views.equipment_report, name='equipment_report'),
path('reports/equipment-by-status/', views.equipment_by_status_report, name='equipment_by_status_report'),
path('reports/ppm-schedule/', views.ppm_schedule_report, name='ppm_schedule_report'),
path('reports/equipment-by-department/', views.equipment_by_department_report, name='equipment_by_department_report'),



]