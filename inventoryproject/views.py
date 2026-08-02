# inventoryproject/views.py

from django.shortcuts import render


def custom_403(request, exception=None):
    """Custom 403 error page handler"""
    return render(request, '403.html', {
        'user': request.user
    }, status=403)


def custom_404(request, exception=None):
    """Custom 404 error page handler"""
    return render(request, 'partials/404.html', {
        'user': request.user
    }, status=404)