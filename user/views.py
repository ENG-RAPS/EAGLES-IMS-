# user/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetConfirmView
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.urls import reverse_lazy

from .forms import CreateUserForm, UserUpdateForm, ProfileUpdateForm
from .models import Profile, Branch, Department


# ---------- USER REGISTRATION (Admin only) ----------
def register(request):
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('dashboard-index')

    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            # Assign a default role and group (e.g., STORE_OFFICER)
            # You can change this based on your requirements
            default_role = 'STORE_OFFICER'
            new_user.profile.role = default_role
            new_user.profile.save()
            # Add to default group
            group, _ = Group.objects.get_or_create(name=default_role)
            new_user.groups.add(group)
            messages.success(request, f'Account created for {new_user.username}. You can now login.')
            return redirect('user:login')
    else:
        form = CreateUserForm()
    return render(request, 'user/register.html', {'form': form})



# ---------- PROFILE ----------
@login_required
def profile(request):
    return render(request, 'user/profile.html')


@login_required
def profile_update(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, 
                                   instance=request.user.profile, 
                                   user=request.user)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('user:profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile, user=request.user)
    context = {'u_form': u_form, 'p_form': p_form}
    return render(request, 'user/profile_update.html', context)


# ---------- USER LIST (Admin only) ----------
@login_required
@permission_required('auth.view_user', raise_exception=True)
def user_list(request):
    users = User.objects.all().select_related('profile')
    return render(request, 'user/user_list.html', {'users': users})


# ---------- CUSTOM LOGIN WITH SIMPLE REDIRECT ----------
class CustomLoginView(LoginView):
    template_name = 'user/login.html'

    def get_success_url(self):
        redirect_to = self.request.GET.get('next')
        if redirect_to:
            print(f"🔀 Login redirects to 'next': {redirect_to}")
            return redirect_to
        print(f"🔀 Login redirects to dashboard-index")
        return reverse_lazy('dashboard-index')

# ---------- PASSWORD RESET (Django built-in) ----------
class CustomPasswordResetView(PasswordResetView):
    template_name = 'user/password_reset.html'
    email_template_name = 'user/password_reset_email.html'
    subject_template_name = 'user/password_reset_subject.txt'
    success_url = reverse_lazy('user:password-reset-done')


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'user/password_reset_confirm.html'
    success_url = reverse_lazy('user:password-reset-complete')