from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('mark-read/<int:pk>/', views.mark_read, name='mark-read'),
]