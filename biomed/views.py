# biomed/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone

from .models import (
    BiomedCategory,
    Equipment,
    CorrectiveMaintenance,
    PPM,
    Department,
    EquipmentStockTake,
    EquipmentTransfer,
    EQUIPMENT_STATUS,
)
from .forms import (
    EquipmentForm,
    EquipmentTransferForm,
    PPMForm,
    StockTakeForm,
    BiomedCategoryForm,
    CorrectiveMaintenanceForm,
)
from .service import create_corrective, set_ppm_status
from user.models import Branch, Profile

# Import all forms
from .forms import (
    EquipmentForm,
    EquipmentTransferForm,
    PPMForm,
    StockTakeForm,
    BiomedCategoryForm,      # <-- ADDED
)

from user.models import Branch, Profile


# ---------- EQUIPMENT CRUD ----------
@login_required
def equipment_list(request):
    user = request.user
    branch = Profile.objects.get(user=user).branch
    if user.is_superuser:
        equipments = Equipment.objects.all()
    else:
        equipments = Equipment.objects.filter(branch=branch)

    query = request.GET.get('q')
    if query:
        equipments = equipments.filter(
            Q(equipment_name__icontains=query) |
            Q(serial_number__icontains=query) |
            Q(asset_tag__icontains=query)
        )

    status_filter = request.GET.get('status')
    if status_filter:
        equipments = equipments.filter(status=status_filter)

    paginator = Paginator(equipments, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'equipments': page_obj,
        'query': query,
        'status_filter': status_filter,
        'status_choices': EQUIPMENT_STATUS,
    }
    return render(request, 'biomed/equipment_list.html', context)


@login_required
@permission_required('biomed.add_equipment', raise_exception=True)
def equipment_create(request):
    if request.method == 'POST':
        form = EquipmentForm(request.POST)
        if form.is_valid():
            eq = form.save(commit=False)
            eq.branch = Profile.objects.get(user=request.user).branch
            eq.created_by = request.user
            eq.save()
            messages.success(request, 'Equipment added successfully.')
            return redirect('biomed:equipment_list')
    else:
        form = EquipmentForm()
    return render(request, 'biomed/equipment_form.html', {'form': form, 'title': 'Add Equipment'})


@login_required
@permission_required('biomed.change_equipment', raise_exception=True)
def equipment_edit(request, pk):
    eq = get_object_or_404(Equipment, pk=pk)
    if request.method == 'POST':
        form = EquipmentForm(request.POST, instance=eq)
        if form.is_valid():
            form.save()
            messages.success(request, 'Equipment updated successfully.')
            return redirect('biomed:equipment_list')
    else:
        form = EquipmentForm(instance=eq)
    return render(request, 'biomed/equipment_form.html', {'form': form, 'title': 'Edit Equipment'})


@login_required
@permission_required('biomed.delete_equipment', raise_exception=True)
def equipment_delete(request, pk):
    eq = get_object_or_404(Equipment, pk=pk)
    if request.method == 'POST':
        eq.delete()
        messages.success(request, 'Equipment deleted successfully.')
        return redirect('biomed:equipment_list')
    return render(request, 'biomed/equipment_confirm_delete.html', {'equipment': eq})


@login_required
def equipment_detail(request, pk):
    eq = get_object_or_404(Equipment, pk=pk)
    ppms = PPM.objects.filter(equipment=eq)
    stocktakes = EquipmentStockTake.objects.filter(equipment=eq)
    context = {
        'equipment': eq,
        'ppms': ppms,
        'stocktakes': stocktakes,
    }
    return render(request, 'biomed/equipment_detail.html', context)


# ---------- PPM CRUD ----------
@login_required
def ppm_list(request):
    user = request.user
    branch = Profile.objects.get(user=user).branch
    if user.is_superuser:
        ppms = PPM.objects.all()
    else:
        ppms = PPM.objects.filter(equipment__branch=branch)

    query = request.GET.get('q')
    if query:
        ppms = ppms.filter(equipment__equipment_name__icontains=query)

    status_filter = request.GET.get('status')
    if status_filter:
        ppms = ppms.filter(status=status_filter)

    paginator = Paginator(ppms, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'ppms': page_obj,
        'query': query,
        'status_filter': status_filter,
        'ppm_status_choices': PPM.PPM_STATUS,
    }
    return render(request, 'biomed/ppm_list.html', context)


@login_required
@permission_required('biomed.add_ppm', raise_exception=True)
def ppm_create(request):
    if request.method == 'POST':
        form = PPMForm(request.POST)
        if form.is_valid():
            ppm = form.save(commit=False)
            ppm.serial_number = ppm.equipment.serial_number
            ppm.model_number = ppm.equipment.model_number
            ppm.location = ppm.equipment.location
            ppm.created_by = request.user
            ppm.save()
            messages.success(request, 'PPM scheduled successfully.')
            return redirect('biomed:ppm_list')
    else:
        form = PPMForm()
    return render(request, 'biomed/ppm_form.html', {'form': form, 'title': 'Schedule PPM'})


@login_required
@permission_required('biomed.change_ppm', raise_exception=True)
def ppm_edit(request, pk):
    ppm = get_object_or_404(PPM, pk=pk)
    if request.method == 'POST':
        form = PPMForm(request.POST, instance=ppm)
        if form.is_valid():
            form.save()
            messages.success(request, 'PPM updated successfully.')
            return redirect('biomed:ppm_list')
    else:
        form = PPMForm(instance=ppm)
    return render(request, 'biomed/ppm_form.html', {'form': form, 'title': 'Edit PPM'})


@login_required
@permission_required('biomed.delete_ppm', raise_exception=True)
def ppm_delete(request, pk):
    ppm = get_object_or_404(PPM, pk=pk)
    if request.method == 'POST':
        ppm.delete()
        messages.success(request, 'PPM deleted successfully.')
        return redirect('biomed:ppm_list')
    return render(request, 'biomed/ppm_confirm_delete.html', {'ppm': ppm})


@login_required
def ppm_detail(request, pk):
    ppm = get_object_or_404(PPM, pk=pk)
    return render(request, 'biomed/ppm_detail.html', {'ppm': ppm})


# ---------- STOCKTAKE CRUD ----------
@login_required
def stocktake_list(request):
    user = request.user
    branch = Profile.objects.get(user=user).branch
    if user.is_superuser:
        stocktakes = EquipmentStockTake.objects.all()
    else:
        stocktakes = EquipmentStockTake.objects.filter(branch=branch)

    query = request.GET.get('q')
    if query:
        stocktakes = stocktakes.filter(equipment__equipment_name__icontains=query)

    condition_filter = request.GET.get('condition')
    if condition_filter:
        stocktakes = stocktakes.filter(condition=condition_filter)

    paginator = Paginator(stocktakes, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'stocktakes': page_obj,
        'query': query,
        'condition_filter': condition_filter,
        'condition_choices': EquipmentStockTake.CONDITION_CHOICES,
    }
    return render(request, 'biomed/stocktake_list.html', context)


@login_required
@permission_required('biomed.add_stocktake', raise_exception=True)
def stocktake_create(request):
    if request.method == 'POST':
        form = StockTakeForm(request.POST)
        if form.is_valid():
            st = form.save(commit=False)
            st.branch = Profile.objects.get(user=request.user).branch
            st.performed_by = request.user
            st.save()
            messages.success(request, 'Stock take recorded successfully.')
            return redirect('biomed:stocktake_list')
    else:
        form = StockTakeForm()
    return render(request, 'biomed/stocktake_form.html', {'form': form, 'title': 'Record Stock Take'})


@login_required
@permission_required('biomed.change_stocktake', raise_exception=True)
def stocktake_edit(request, pk):
    st = get_object_or_404(EquipmentStockTake, pk=pk)
    if request.method == 'POST':
        form = StockTakeForm(request.POST, instance=st)
        if form.is_valid():
            form.save()
            messages.success(request, 'Stock take updated successfully.')
            return redirect('biomed:stocktake_list')
    else:
        form = StockTakeForm(instance=st)
    return render(request, 'biomed/stocktake_form.html', {'form': form, 'title': 'Edit Stock Take'})


@login_required
@permission_required('biomed.delete_stocktake', raise_exception=True)
def stocktake_delete(request, pk):
    st = get_object_or_404(EquipmentStockTake, pk=pk)
    if request.method == 'POST':
        st.delete()
        messages.success(request, 'Stock take deleted successfully.')
        return redirect('biomed:stocktake_list')
    return render(request, 'biomed/stocktake_confirm_delete.html', {'stocktake': st})


@login_required
def stocktake_detail(request, pk):
    st = get_object_or_404(EquipmentStockTake, pk=pk)
    return render(request, 'biomed/stocktake_detail.html', {'stocktake': st})


# ---------- EQUIPMENT TRANSFER ----------
@login_required
def transfer_list(request):
    user = request.user
    branch = Profile.objects.get(user=user).branch
    if user.is_superuser:
        transfers = EquipmentTransfer.objects.all().order_by('-transfer_date')
    else:
        transfers = EquipmentTransfer.objects.filter(
            Q(from_branch=branch) | Q(to_branch=branch) | Q(requested_by=user)
        ).order_by('-transfer_date')

    query = request.GET.get('q')
    if query:
        transfers = transfers.filter(equipment__equipment_name__icontains=query)

    status_filter = request.GET.get('status')
    if status_filter:
        transfers = transfers.filter(status=status_filter)

    paginator = Paginator(transfers, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'transfers': page_obj,
        'query': query,
        'status_filter': status_filter,
        'status_choices': EquipmentTransfer.TRANSFER_STATUS,
    }
    return render(request, 'biomed/transfer_list.html', context)


@login_required
@permission_required('biomed.add_equipmenttransfer', raise_exception=True)
def transfer_create(request):
    if request.method == 'POST':
        form = EquipmentTransferForm(request.POST, user=request.user)
        if form.is_valid():
            transfer = form.save(commit=False)
            transfer.from_branch = Profile.objects.get(user=request.user).branch
            transfer.requested_by = request.user
            transfer.save()
            messages.success(request, 'Transfer request created. Awaiting approval.')
            return redirect('biomed:transfer_list')
    else:
        form = EquipmentTransferForm(user=request.user)
    return render(request, 'biomed/transfer_form.html', {'form': form, 'title': 'Request Equipment Transfer'})


@login_required
@permission_required('biomed.change_equipmenttransfer', raise_exception=True)
def transfer_approve(request, pk):
    transfer = get_object_or_404(EquipmentTransfer, pk=pk)
    if transfer.status != 'PENDING':
        messages.warning(request, 'This transfer is no longer pending.')
        return redirect('biomed:transfer_list')

    if request.method == 'POST':
        if transfer.approve(request.user):
            messages.success(request, f'Transfer approved. Equipment moved to {transfer.to_branch.name}.')
        else:
            messages.error(request, 'Approval failed.')
        return redirect('biomed:transfer_list')

    return render(request, 'biomed/transfer_approve.html', {'transfer': transfer})


@login_required
@permission_required('biomed.delete_equipmenttransfer', raise_exception=True)
def transfer_reject(request, pk):
    transfer = get_object_or_404(EquipmentTransfer, pk=pk)
    if transfer.status != 'PENDING':
        messages.warning(request, 'This transfer is no longer pending.')
        return redirect('biomed:transfer_list')

    if request.method == 'POST':
        transfer.status = 'REJECTED'
        transfer.approved_by = request.user
        transfer.save()
        messages.success(request, 'Transfer rejected.')
        return redirect('biomed:transfer_list')

    return render(request, 'biomed/transfer_reject.html', {'transfer': transfer})


@login_required
def transfer_detail(request, pk):
    transfer = get_object_or_404(EquipmentTransfer, pk=pk)
    return render(request, 'biomed/transfer_detail.html', {'transfer': transfer})


# ---------- BIOMED CATEGORY CRUD ----------
@login_required
def category_list(request):
    categories = BiomedCategory.objects.all().order_by('name')
    return render(request, 'biomed/category_list.html', {'categories': categories})


@login_required
@permission_required('biomed.add_biomedcategory', raise_exception=True)
def category_create(request):
    if request.method == 'POST':
        form = BiomedCategoryForm(request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.created_by = request.user
            cat.save()
            messages.success(request, 'Category added successfully.')
            return redirect('biomed:category_list')
    else:
        form = BiomedCategoryForm()
    return render(request, 'biomed/category_form.html', {'form': form, 'title': 'Add Category'})


@login_required
@permission_required('biomed.change_biomedcategory', raise_exception=True)
def category_edit(request, pk):
    cat = get_object_or_404(BiomedCategory, pk=pk)
    if request.method == 'POST':
        form = BiomedCategoryForm(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully.')
            return redirect('biomed:category_list')
    else:
        form = BiomedCategoryForm(instance=cat)
    return render(request, 'biomed/category_form.html', {'form': form, 'title': 'Edit Category'})


@login_required
@permission_required('biomed.delete_biomedcategory', raise_exception=True)
def category_delete(request, pk):
    cat = get_object_or_404(BiomedCategory, pk=pk)
    if request.method == 'POST':
        cat.delete()
        messages.success(request, 'Category deleted successfully.')
        return redirect('biomed:category_list')
    return render(request, 'biomed/category_confirm_delete.html', {'category': cat})



# ---------- Equipment Report ----------
@login_required
@permission_required('biomed.view_equipment', raise_exception=True)
def equipment_report(request):
    user = request.user
    profile = user.profile
    queryset = Equipment.objects.select_related('category', 'department', 'branch')
    if not user.is_superuser and profile.role != 'MAIN_ADMIN':
        queryset = queryset.filter(branch=profile.branch)

    # Search
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(equipment_name__icontains=search) |
            Q(model_number__icontains=search) |
            Q(serial_number__icontains=search) |
            Q(asset_tag__icontains=search)
        )

    # Filters
    category_id = request.GET.get('category')
    if category_id:
        queryset = queryset.filter(category_id=category_id)

    status = request.GET.get('status')
    if status:
        queryset = queryset.filter(status=status)

    department_id = request.GET.get('department')
    if department_id:
        queryset = queryset.filter(department_id=department_id)

    # Sorting
    sort = request.GET.get('sort', 'equipment_name')
    allowed_sorts = ['equipment_name', 'model_number', 'status', 'department__name', 'category__name']
    if sort not in allowed_sorts:
        sort = 'equipment_name'
    queryset = queryset.order_by(sort)

    paginator = Paginator(queryset, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search': search,
        'category_id': category_id,
        'status': status,
        'department_id': department_id,
        'sort': sort,
        'categories': BiomedCategory.objects.all(),  # ensure Category exists in biomed
        'departments': Department.objects.all(),
        'status_choices': EQUIPMENT_STATUS,
    }
    return render(request, 'biomed/equipment_report.html', context)


# ---------- Equipment by Status Report ----------
@login_required
@permission_required('biomed.view_equipment', raise_exception=True)
def equipment_by_status_report(request):
    user = request.user
    profile = user.profile
    queryset = Equipment.objects.all()
    if not user.is_superuser and profile.role != 'MAIN_ADMIN':
        queryset = queryset.filter(branch=profile.branch)

    # Group by status
    status_counts = queryset.values('status').annotate(count=Count('id')).order_by('status')

    # If you have STATUS_CHOICES, map labels
    status_labels = dict(Equipment.STATUS_CHOICES) if hasattr(Equipment, 'STATUS_CHOICES') else {}
    for item in status_counts:
        item['status_label'] = status_labels.get(item['status'], item['status'])

    context = {
        'status_counts': status_counts,
        'total': queryset.count(),
    }
    return render(request, 'biomed/equipment_by_status_report.html', context)


# ---------- PPM Schedule Report ----------
@login_required
@permission_required('biomed.view_ppm', raise_exception=True)
def ppm_schedule_report(request):
    user = request.user
    profile = user.profile
    queryset = PPM.objects.select_related('equipment')
    if not user.is_superuser and profile.role != 'MAIN_ADMIN':
        queryset = queryset.filter(equipment__branch=profile.branch)

    # Date filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        queryset = queryset.filter(ppm_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(ppm_date__lte=end_date)

    # Status filter
    status = request.GET.get('status')
    if status:
        queryset = queryset.filter(status=status)

    # Search by equipment name
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(equipment__name__icontains=search)

    queryset = queryset.order_by('ppm_date')

    paginator = Paginator(queryset, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'start_date': start_date,
        'end_date': end_date,
        'status': status,
        'search': search,
        'status_choices': PPM.STATUS_CHOICES if hasattr(PPM, 'STATUS_CHOICES') else [],
    }
    return render(request, 'biomed/ppm_schedule_report.html', context)


# ---------- Equipment by Department Report ----------
@login_required
@permission_required('biomed.view_equipment', raise_exception=True)
def equipment_by_department_report(request):
    user = request.user
    profile = user.profile
    queryset = Equipment.objects.select_related('department')
    if not user.is_superuser and profile.role != 'MAIN_ADMIN':
        queryset = queryset.filter(branch=profile.branch)

    # Group by department
    dept_counts = queryset.values('department__name').annotate(count=Count('id')).order_by('-count')

    paginator = Paginator(dept_counts, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'total': queryset.count(),
    }
    return render(request, 'biomed/equipment_by_department_report.html', context)


# ---------- CORRECTIVE MAINTENANCE ----------
@login_required
def corrective_list(request):
    user = request.user
    branch = Profile.objects.get(user=user).branch
    if user.is_superuser:
        cms = CorrectiveMaintenance.objects.select_related('equipment').all()
    else:
        cms = CorrectiveMaintenance.objects.filter(equipment__branch=branch)

    paginator = Paginator(cms.order_by('-date'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'biomed/corrective_list.html', {'cms': page_obj})


@login_required
@permission_required('biomed.add_correctivemaintenance', raise_exception=True)
def corrective_create(request):
    if request.method == 'POST':
        form = CorrectiveMaintenanceForm(request.POST)
        if form.is_valid():
            cm = form.save(commit=False)
            cm.processed_by = request.user
            cm.save()
            messages.success(request, 'Corrective maintenance record created.')
            return redirect('biomed:corrective_list')
    else:
        form = CorrectiveMaintenanceForm()
    return render(request, 'biomed/corrective_form.html', {'form': form, 'title': 'Add Corrective Maintenance'})


@login_required
def corrective_detail(request, pk):
    cm = get_object_or_404(CorrectiveMaintenance, pk=pk)
    return render(request, 'biomed/corrective_detail.html', {'cm': cm})


@login_required
@permission_required('biomed.change_correctivemaintenance', raise_exception=True)
def corrective_edit(request, pk):
    cm = get_object_or_404(CorrectiveMaintenance, pk=pk)
    if request.method == 'POST':
        form = CorrectiveMaintenanceForm(request.POST, instance=cm)
        if form.is_valid():
            form.save()
            messages.success(request, 'Corrective maintenance record updated.')
            return redirect('biomed:corrective_detail', pk=cm.pk)
    else:
        form = CorrectiveMaintenanceForm(instance=cm)
    return render(request, 'biomed/corrective_form.html', {'form': form, 'title': 'Edit Corrective Maintenance'})


@login_required
@permission_required('biomed.delete_correctivemaintenance', raise_exception=True)
def corrective_delete(request, pk):
    cm = get_object_or_404(CorrectiveMaintenance, pk=pk)
    if request.method == 'POST':
        cm.delete()
        messages.success(request, 'Corrective maintenance record deleted.')
        return redirect('biomed:corrective_list')
    return render(request, 'biomed/corrective_confirm_delete.html', {'cm': cm})


# ---------- PPM Quick Status Change (AJAX) ----------
@login_required
@permission_required('biomed.change_ppm', raise_exception=True)
def ppm_set_status(request, pk):
    if request.method != 'POST':
        return redirect('biomed:ppm_list')
    status = request.POST.get('status')
    try:
        ppm = set_ppm_status(pk, status, user=request.user)
        messages.success(request, f'PPM status updated to {status}.')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('biomed:ppm_list')