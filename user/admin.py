# user/admin.py
from django.contrib import admin
from .models import Branch, Department, Profile


class DepartmentInline(admin.TabularInline):
    """Allows adding/editing Departments directly from the Branch admin page."""
    model = Department
    extra = 1
    fields = ('name',)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'phone', 'email', 'status')
    search_fields = ('name', 'location')
    list_filter = ('status',)
    inlines = [DepartmentInline]   # <-- shows Departments inline


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch')
    list_filter = ('branch',)
    search_fields = ('name',)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'branch', 'department', 'status')
    list_filter = ('role', 'branch', 'department', 'status')
    search_fields = ('user__username', 'user__email')