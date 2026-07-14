# biomed/admin.py
from django.contrib import admin
from .models import (
    BiomedCategory,
    Equipment,
    PPM,
    EquipmentStockTake,
    EquipmentTransfer,
)


@admin.register(BiomedCategory)
class BiomedCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = [
        'equipment_name', 'serial_number', 'asset_tag', 
        'status', 'branch', 'department', 'date_added'
    ]
    search_fields = ['equipment_name', 'serial_number', 'asset_tag']
    list_filter = ['status', 'branch', 'department', 'category']
    readonly_fields = ['date_added', 'created_by']
    fieldsets = (
        ('Basic Information', {
            'fields': ('equipment_name', 'category', 'manufacturer', 'model_number')
        }),
        ('Identification', {
            'fields': ('serial_number', 'asset_tag')
        }),
        ('Purchase Details', {
            'fields': ('purchase_date', 'purchase_cost', 'supplier', 'warranty_expiry')
        }),
        ('Location & Status', {
            'fields': ('branch', 'department', 'location', 'status')
        }),
        ('Audit', {
            'fields': ('date_added', 'created_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PPM)
class PPMAdmin(admin.ModelAdmin):
    list_display = [
        'equipment', 'ppm_date', 'next_ppm_date', 'status', 'technician'
    ]
    search_fields = ['equipment__equipment_name', 'serial_number']
    list_filter = ['status', 'ppm_date', 'technician']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    fieldsets = (
        ('Equipment', {
            'fields': ('equipment', 'serial_number', 'model_number', 'location')
        }),
        ('Maintenance Dates', {
            'fields': ('previous_ppm_date', 'ppm_date', 'next_ppm_date')
        }),
        ('Assignment', {
            'fields': ('technician', 'status', 'remarks')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EquipmentStockTake)
class EquipmentStockTakeAdmin(admin.ModelAdmin):
    list_display = ['equipment', 'date', 'condition', 'performed_by', 'branch']
    search_fields = ['equipment__equipment_name']
    list_filter = ['condition', 'date', 'branch']
    readonly_fields = ['created_at', 'updated_at']
    fields = ('equipment', 'branch', 'date', 'condition', 'remarks', 'performed_by', 'created_at', 'updated_at')


@admin.register(EquipmentTransfer)
class EquipmentTransferAdmin(admin.ModelAdmin):
    list_display = [
        'equipment', 'from_branch', 'to_branch', 'status', 
        'requested_by', 'transfer_date'
    ]
    search_fields = ['equipment__equipment_name']
    list_filter = ['status', 'from_branch', 'to_branch', 'transfer_date']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Transfer Details', {
            'fields': ('equipment', 'from_branch', 'to_branch')
        }),
        ('Approval', {
            'fields': ('requested_by', 'approved_by', 'status', 'remarks')
        }),
        ('Dates', {
            'fields': ('transfer_date', 'created_at', 'updated_at')
        }),
    )