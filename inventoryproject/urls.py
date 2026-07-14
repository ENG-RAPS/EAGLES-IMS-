from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.urls import get_resolver
urlpatterns = [
    # ---- ROOT MUST BE DASHBOARD ----
    path('', include('dashboard.urls')),          # <-- MUST BE FIRST

    # ---- OTHER APPS (sub‑paths) ----
    path('user/', include('user.urls')),
    path('store/', include('store.urls')),
    path('biomed/', include('biomed.urls')),
    path('notifications/', include('notifications.urls')), 

    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    

