# inventoryproject/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from .views import custom_403, custom_404  # type: ignore

handler403 = custom_403
handler404 = custom_404

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

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG or 'localhost' in settings.ALLOWED_HOSTS or '127.0.0.1' in settings.ALLOWED_HOSTS:
    urlpatterns += staticfiles_urlpatterns()
    
    