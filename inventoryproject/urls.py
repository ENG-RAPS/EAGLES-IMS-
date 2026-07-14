# inventoryproject/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Redirect /login to /user/login/
    path('login/', RedirectView.as_view(url='/user/login/', permanent=True)),

    # Your apps
    path('', include('dashboard.urls')),
    path('user/', include('user.urls')),
    path('store/', include('store.urls')),
    path('biomed/', include('biomed.urls')),
    path('notifications/', include('notifications.urls')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    