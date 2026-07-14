# user/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetConfirmView
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.conf import settings
# Check for related records
from user.models import Profile
from store.models import Product, StockTransaction
from biomed.models import Equipment
from .forms import CreateUserForm, UserUpdateForm, ProfileUpdateForm
from .models import Profile, Branch, Department


# ---------- USER REGISTRATION (with admin approval) ----------
def register(request):
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('dashboard-index')

    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.is_active = False          # 🔒 Inactive until approved
            new_user.save()

            # Assign a default role (you can change this)
            default_role = 'STORE_OFFICER'
            new_user.profile.role = default_role
            new_user.profile.save()

            # Add to default group
            group, _ = Group.objects.get_or_create(name=default_role)
            new_user.groups.add(group)

            # Optional: send email to admins (see below)
            messages.success(
                request,
                f'Account created for {new_user.username}. Please wait for admin approval before logging in.'
            )
            return redirect('user:login')
    else:
        form = CreateUserForm()
    return render(request, 'user/register.html', {'form': form})


# ---------- ACTIVATE USER (Admin only) ----------
@login_required
@permission_required('auth.change_user', raise_exception=True)
def activate_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.is_active:
        messages.warning(request, f'{user.username} is already active.')
    else:
        user.is_active = True
        user.save()
        messages.success(request, f'User {user.username} has been activated successfully.')
    return redirect('user:list')   # <-- changed from 'user:user_list' to 'user:list'


@login_required
@permission_required('auth.change_user', raise_exception=True)
def deactivate_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.is_superuser:
        messages.error(request, 'Cannot deactivate a superuser.')
    else:
        user.is_active = False
        user.save()
        messages.success(request, f'User {user.username} has been deactivated.')
    return redirect('user:list')   # <-- changed from 'user:user_list' to 'user:list'


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
    users = User.objects.all().select_related('profile').order_by('-date_joined')
    return render(request, 'user/user_list.html', {'users': users})


# ---------- CUSTOM LOGIN WITH SIMPLE REDIRECT ----------
class CustomLoginView(LoginView):
    template_name = 'user/login.html'

    def get_success_url(self):
        redirect_to = self.request.GET.get('next')
        if redirect_to:
            return redirect_to
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
    
    # ---------- BRANCH MANAGEMENT (Admin only) ----------
@login_required
@permission_required('user.view_branch', raise_exception=True)
def branch_list(request):
    branches = Branch.objects.all().order_by('name')
    return render(request, 'user/branch_list.html', {'branches': branches})

@login_required
@permission_required('user.add_branch', raise_exception=True)
def branch_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        location = request.POST.get('location')
        phone = request.POST.get('phone', '')
        email = request.POST.get('email', '')
        status = request.POST.get('status') == 'on'
        if name and location:
            Branch.objects.create(name=name, location=location, phone=phone, email=email, status=status)
            messages.success(request, f'Branch "{name}" created successfully.')
            return redirect('user:branch_list')
        else:
            messages.error(request, 'Name and Location are required.')
    return render(request, 'user/branch_form.html', {'title': 'Add Branch'})

@login_required
@permission_required('user.change_branch', raise_exception=True)
def branch_edit(request, branch_id):
    branch = get_object_or_404(Branch, id=branch_id)
    if request.method == 'POST':
        branch.name = request.POST.get('name')
        branch.location = request.POST.get('location')
        branch.phone = request.POST.get('phone', '')
        branch.email = request.POST.get('email', '')
        branch.status = request.POST.get('status') == 'on'
        branch.save()
        messages.success(request, f'Branch "{branch.name}" updated successfully.')
        return redirect('user:branch_list')
    return render(request, 'user/branch_form.html', {'branch': branch, 'title': 'Edit Branch'})

@login_required
@permission_required('user.delete_branch', raise_exception=True)
def branch_delete(request, branch_id):
    branch = get_object_or_404(Branch, id=branch_id)
    
    related_profiles = Profile.objects.filter(branch=branch).count()
    related_products = Product.objects.filter(branch=branch).count()
    related_equipment = Equipment.objects.filter(branch=branch).count()
    
    if request.method == 'POST':
        if related_profiles > 0 or related_products > 0 or related_equipment > 0:
            messages.error(
                request,
                f'Cannot delete "{branch.name}" – it has {related_profiles} profile(s), {related_products} product(s), and {related_equipment} equipment(s) linked to it.'
            )
            return redirect('user:branch_list')
        
        branch.delete()
        messages.success(request, f'Branch "{branch.name}" deleted.')
        return redirect('user:branch_list')
    
    return render(request, 'user/branch_confirm_delete.html', {
        'branch': branch,
        'related_profiles': related_profiles,
        'related_products': related_products,
        'related_equipment': related_equipment,
    })
    
    
# ---------- DEPARTMENT MANAGEMENT (Admin only) ----------
@login_required
@permission_required('user.view_department', raise_exception=True)
def department_list(request):
    departments = Department.objects.select_related('branch').all().order_by('name')
    return render(request, 'user/department_list.html', {'departments': departments})

@login_required
@permission_required('user.add_department', raise_exception=True)
def department_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        branch_id = request.POST.get('branch')
        if name and branch_id:
            branch = get_object_or_404(Branch, id=branch_id)
            Department.objects.create(name=name, branch=branch)
            messages.success(request, f'Department "{name}" created successfully.')
            return redirect('user:department_list')
        else:
            messages.error(request, 'Name and Branch are required.')
    branches = Branch.objects.filter(status=True)
    return render(request, 'user/department_form.html', {'branches': branches, 'title': 'Add Department'})

@login_required
@permission_required('user.change_department', raise_exception=True)
def department_edit(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    if request.method == 'POST':
        department.name = request.POST.get('name')
        branch_id = request.POST.get('branch')
        if branch_id:
            department.branch = get_object_or_404(Branch, id=branch_id)
        department.save()
        messages.success(request, f'Department "{department.name}" updated successfully.')
        return redirect('user:department_list')
    branches = Branch.objects.filter(status=True)
    return render(request, 'user/department_form.html', {
        'department': department,
        'branches': branches,
        'title': 'Edit Department'
    })

@login_required
@permission_required('user.delete_department', raise_exception=True)
def department_delete(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    if request.method == 'POST':
        department.delete()
        messages.success(request, f'Department "{department.name}" deleted.')
        return redirect('user:department_list')
    return render(request, 'user/department_confirm_delete.html', {'department': department})