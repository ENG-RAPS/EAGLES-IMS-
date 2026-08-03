# user/admin.py
from django.contrib import admin, messages
from django.db.models.deletion import ProtectedError
from django.shortcuts import redirect
from .models import Branch, Department, Profile


class DepartmentInline(admin.TabularInline):
    """Allows adding/editing Departments directly from the Branch admin page."""
    model = Department
    extra = 1
    fields = ('name',)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'phone', 'email', 'status', 'logo')
    search_fields = ('name', 'location')
    list_filter = ('status',)
    fields = ('name', 'location', 'phone', 'email', 'status', 'logo')
    inlines = [DepartmentInline]   # <-- shows Departments inline

    def delete_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, object_id)
        if request.method == 'POST' and obj is not None:
            try:
                return super().delete_view(request, object_id, extra_context=extra_context)
            except ProtectedError as exc:
                self.message_user(request, str(exc), level=messages.ERROR)
                return redirect('admin:user_branch_change', object_id)
        return super().delete_view(request, object_id, extra_context=extra_context)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            try:
                obj.delete()
            except ProtectedError as exc:
                self.message_user(request, str(exc), level=messages.ERROR)


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