from django.shortcuts import get_object_or_404, redirect, render

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Notification


@login_required
def inbox(request):
    notifications = request.user.notifications.all()
    unread_count = notifications.filter(is_read=False).count()
    return render(request, 'notifications/inbox.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })

@login_required
def mark_read(request, pk):
    notify = get_object_or_404(Notification, pk=pk, user=request.user)
    notify.is_read = True
    notify.save()
    return redirect('notifications:inbox')