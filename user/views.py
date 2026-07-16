# user/views.py - COMPLETE WORKING VERSION WITH ROLE SELECTION

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetConfirmView
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

# Check for related records
from user.models import Profile
from store.models import Product, StockTransaction
from biomed.models import Equipment
from .forms import CreateUserForm, UserUpdateForm, ProfileUpdateForm
from .models import Profile, Branch, Department, TransferRequest, ROLE_CHOICES


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

            # ✅ Get the selected role from form
            selected_role = form.cleaned_data.get('role', 'STORE_OFFICER')
            selected_branch = form.cleaned_data.get('branch')
            selected_department = form.cleaned_data.get('department')

            # ✅ Create profile with the SELECTED role (NOT hardcoded)
            profile, created = Profile.objects.get_or_create(
                user=new_user,
                defaults={
                    'role': selected_role,  # 👈 NOW USES SELECTED ROLE
                    'status': True,
                    'address': '',
                    'phone': '',
                    'image': 'default.png',
                    'branch': selected_branch,
                    'department': selected_department,
                }
            )

            # ✅ Add to the corresponding group
            group, _ = Group.objects.get_or_create(name=selected_role)
            new_user.groups.add(group)

            messages.success(
                request,
                f'Account created for {new_user.username} as {selected_role}. Please wait for admin approval before logging in.'
            )
            return redirect('user:login')
        else:
            messages.error(request, 'Please correct the errors below.')
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
    return redirect('user:list')


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
    return redirect('user:list')


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


# ---------- TRANSFER USER (Admin only) ----------
@login_required
@permission_required('user.change_profile', raise_exception=True)
def transfer_user_branch(request, user_id):
    """Transfer a user to a different branch"""
    user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(Profile, user=user)
    
    if request.method == 'POST':
        new_branch_id = request.POST.get('branch')
        new_department_id = request.POST.get('department')
        new_role = request.POST.get('role')
        
        if new_branch_id:
            new_branch = get_object_or_404(Branch, id=new_branch_id)
            profile.branch = new_branch
            profile.save()
            
            # Update department if provided
            if new_department_id:
                new_department = get_object_or_404(Department, id=new_department_id)
                profile.department = new_department
                profile.save()
            
            # Update role if provided
            if new_role:
                profile.role = new_role
                profile.save()
                
                # Update group
                user.groups.clear()
                group, _ = Group.objects.get_or_create(name=new_role)
                user.groups.add(group)
            
            messages.success(
                request, 
                f'User {user.username} has been transferred to {new_branch.name} branch.'
            )
            return redirect('user:list')
        else:
            messages.error(request, 'Please select a branch.')
    
    branches = Branch.objects.filter(status=True)
    departments = Department.objects.filter(branch=profile.branch) if profile.branch else Department.objects.none()
    
    context = {
        'user': user,
        'profile': profile,
        'branches': branches,
        'departments': departments,
        'role_choices': ROLE_CHOICES,
    }
    return render(request, 'user/transfer_branch.html', context)


# ---------- REQUEST BRANCH TRANSFER (User self-transfer) ----------
@login_required
def request_branch_transfer(request):
    """Allow user to request branch transfer"""
    profile = request.user.profile
    
    if request.method == 'POST':
        new_branch_id = request.POST.get('branch')
        reason = request.POST.get('reason', '')
        
        if new_branch_id:
            try:
                new_branch = get_object_or_404(Branch, id=new_branch_id)
                
                # Check if already in this branch
                if profile.branch and profile.branch.id == new_branch.id:
                    messages.warning(request, f'You are already in {new_branch.name} branch.')
                    return redirect('user:profile')
                
                # Check if there's already a pending request
                existing_request = TransferRequest.objects.filter(
                    user=request.user,
                    status='PENDING'
                ).first()
                
                if existing_request:
                    messages.warning(
                        request, 
                        'You already have a pending transfer request. Please wait for it to be processed.'
                    )
                    return redirect('user:profile')
                
                # Create transfer request
                TransferRequest.objects.create(
                    user=request.user,
                    from_branch=profile.branch,
                    to_branch=new_branch,
                    reason=reason
                )
                
                messages.success(
                    request, 
                    f'Transfer request submitted to {new_branch.name}. Please wait for admin approval.'
                )
                return redirect('user:profile')
            except Exception as e:
                messages.error(request, f'Error submitting request: {str(e)}')
        else:
            messages.error(request, 'Please select a branch.')
    
    branches = Branch.objects.filter(status=True)
    context = {
        'branches': branches,
        'current_branch': profile.branch,
        'pending_request': TransferRequest.objects.filter(user=request.user, status='PENDING').first(),
    }
    return render(request, 'user/request_transfer.html', context)


# ---------- TRANSFER REQUEST MANAGEMENT (Admin only) ----------
@login_required
@permission_required('user.change_profile', raise_exception=True)
def transfer_requests_list(request):
    """Admin view to see all pending transfer requests"""
    # Get all pending requests
    pending_requests = TransferRequest.objects.filter(status='PENDING').select_related('user', 'from_branch', 'to_branch')
    
    # Get all requests (for history)
    all_requests = TransferRequest.objects.all().select_related('user', 'from_branch', 'to_branch', 'reviewed_by')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        all_requests = all_requests.filter(status=status_filter)
    
    context = {
        'pending_requests': pending_requests,
        'all_requests': all_requests,
        'status_filter': status_filter,
        'pending_count': pending_requests.count(),
        'total_count': all_requests.count(),
    }
    return render(request, 'user/transfer_requests_list.html', context)


@login_required
@permission_required('user.change_profile', raise_exception=True)
def transfer_request_approve(request, request_id):
    """Admin approves a transfer request"""
    transfer = get_object_or_404(TransferRequest, id=request_id)
    
    if transfer.status != 'PENDING':
        messages.warning(request, 'This request has already been processed.')
        return redirect('user:transfer_requests')
    
    if request.method == 'POST':
        try:
            # Update user's branch
            profile = transfer.user.profile
            profile.branch = transfer.to_branch
            profile.save()
            
            # Update transfer request
            transfer.status = 'APPROVED'
            transfer.reviewed_by = request.user
            transfer.reviewed_at = timezone.now()
            transfer.review_notes = request.POST.get('notes', '')
            transfer.save()
            
            messages.success(
                request, 
                f'Transfer approved! {transfer.user.username} has been moved to {transfer.to_branch.name}.'
            )
        except Exception as e:
            messages.error(request, f'Error approving transfer: {str(e)}')
        
        return redirect('user:transfer_requests')
    
    return render(request, 'user/transfer_request_review.html', {
        'transfer': transfer,
        'action': 'approve'
    })


@login_required
@permission_required('user.change_profile', raise_exception=True)
def transfer_request_reject(request, request_id):
    """Admin rejects a transfer request"""
    transfer = get_object_or_404(TransferRequest, id=request_id)
    
    if transfer.status != 'PENDING':
        messages.warning(request, 'This request has already been processed.')
        return redirect('user:transfer_requests')
    
    if request.method == 'POST':
        transfer.status = 'REJECTED'
        transfer.reviewed_by = request.user
        transfer.reviewed_at = timezone.now()
        transfer.review_notes = request.POST.get('notes', '')
        transfer.save()
        
        messages.success(
            request, 
            f'Transfer rejected for {transfer.user.username}.'
        )
        return redirect('user:transfer_requests')
    
    return render(request, 'user/transfer_request_review.html', {
        'transfer': transfer,
        'action': 'reject'
    })


# ---------- GET PENDING TRANSFER COUNT (for sidebar badge) ----------
def get_pending_transfer_count(request):
    """Get count of pending transfer requests for sidebar badge"""
    if request.user.is_authenticated and (request.user.is_superuser or request.user.profile.role == 'MAIN_ADMIN'):
        return TransferRequest.objects.filter(status='PENDING').count()
    return 0