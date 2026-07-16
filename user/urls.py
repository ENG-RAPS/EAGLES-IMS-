# user/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'user'

urlpatterns = [
    # Authentication
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='user/logout.html'), name='logout'),
    path('register/', views.register, name='register'),

    # Profile
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.profile_update, name='profile-update'),

    # User Management (Admin only)
    path('list/', views.user_list, name='list'),
    path('activate/<int:user_id>/', views.activate_user, name='activate-user'),
    path('deactivate/<int:user_id>/', views.deactivate_user, name='deactivate-user'),

    # Password Reset
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password-reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='user/password_reset_done.html'), name='password-reset-done'),
    path('password-reset/confirm/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(template_name='user/password_reset_complete.html'), name='password-reset-complete'),
    
    # Branch Management (Admin only)
    path('branches/', views.branch_list, name='branch_list'),
    path('branches/create/', views.branch_create, name='branch_create'),
    path('branches/edit/<int:branch_id>/', views.branch_edit, name='branch_edit'),
    path('branches/delete/<int:branch_id>/', views.branch_delete, name='branch_delete'),
    
    # ✅ Branch Transfer (Admin only) - ONLY ONE!
    path('transfer/<int:user_id>/', views.transfer_user_branch, name='transfer_branch'),
    
    # ✅ Self Transfer Request (Users)
    path('transfer-request/', views.request_branch_transfer, name='request_transfer'),
    # ... existing URLs ...
    path('transfer-requests/', views.transfer_requests_list, name='transfer_requests'),
    path('transfer-requests/approve/<int:request_id>/', views.transfer_request_approve, name='transfer_request_approve'),
    path('transfer-requests/reject/<int:request_id>/', views.transfer_request_reject, name='transfer_request_reject'),

    
    # Department Management
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/edit/<int:department_id>/', views.department_edit, name='department_edit'),
    path('departments/delete/<int:department_id>/', views.department_delete, name='department_delete'),
]