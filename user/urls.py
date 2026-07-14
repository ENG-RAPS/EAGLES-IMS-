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
   path('profile/', views.profile, name='user-profile'),

    # User List (admin)
    path('list/', views.user_list, name='list'),

    # Password Reset
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password-reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='user/password_reset_done.html'), name='password-reset-done'),
    path('password-reset/confirm/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(template_name='user/password_reset_complete.html'), name='password-reset-complete'),
]