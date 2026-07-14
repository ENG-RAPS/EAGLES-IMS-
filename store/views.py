# store/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from .models import Product, StockTransaction, Category, Supplier
from .forms import ProductForm, TransactionForm
from user.models import Profile, Branch, Department
from django.utils import timezone
from django.db.models import Q, F ,Sum  ,Count
from .forms import ProductForm, TransactionForm, SupplierForm, CategoryForm
from django.core.paginator import Paginator
from .forms import SupplierForm
from datetime import datetime, timedelta





# ---------- PRODUCT CRUD ----------

@login_required
def product_list(request):
    user = request.user
    branch = Profile.objects.get(user=user).branch
    if user.is_superuser:
        products = Product.objects.all()
    else:
        products = Product.objects.filter(branch=branch)

    # Search
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(item_code__icontains=query) |
            Q(category__name__icontains=query)
        )

    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)

    # Pagination (25 per page)
    paginator = Paginator(products, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,                     # paginated object
        'categories': Category.objects.all(),     # for filter dropdown
        'selected_category': category_id,
        'query': query,
    }
    return render(request, 'store/product_list.html', context)


@login_required
def product_create(request):
    # Ensure the user's profile has a branch
    profile = Profile.objects.get(user=request.user)
    if not profile.branch:
        # Assign a default branch (the first one in the database)
        default_branch = Branch.objects.first()
        if default_branch:
            profile.branch = default_branch
            profile.save()
            messages.info(request, f'Your profile was assigned to branch: {default_branch.name}')
        else:
            messages.error(request, 'No branch exists. Please create a branch first.')
            return redirect('store:product_list')  # Or some other page

    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.branch = profile.branch
            product.created_by = request.user
            product.save()
            messages.success(request, f'Product "{product.name}" added successfully!')
            return redirect('store:product_list')
    else:
        form = ProductForm()
    return render(request, 'store/product_form.html', {'form': form, 'title': 'Add Product'})


@permission_required('store.change_product')
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('store:product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'store/product_form.html', {'form': form, 'title': 'Edit Product'})

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, f'Product "{product.name}" deleted!')
        return redirect('store:product_list')
    return render(request, 'store/product_confirm_delete.html', {'product': product})


@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    transactions = StockTransaction.objects.filter(product=product).order_by('-transaction_date')

    context = {
        'product': product,
        'transactions': transactions,
    }

    return render(request, 'store/product_detail.html', context)


@login_required
def low_stock_products(request):
    branch = request.user.profile.branch

    if request.user.is_superuser:
        products = Product.objects.filter(
            quantity__lte=F('minimum_stock_level')
        )
    else:
        products = Product.objects.filter(
            branch=branch,
            quantity__lte=F('minimum_stock_level')
        )

    return render(request, 'store/low_stock.html', {'products': products})



# ---------- TRANSACTION CRUD ----------
@login_required
def transaction_list(request):
    user = request.user
    branch = Profile.objects.get(user=user).branch
    if user.is_superuser:
        transactions = StockTransaction.objects.all().order_by('-transaction_date')
    else:
        transactions = StockTransaction.objects.filter(branch=branch).order_by('-transaction_date')

    # Search by product name
    query = request.GET.get('q')
    if query:
        transactions = transactions.filter(product__name__icontains=query)

    # Filter by status
    status = request.GET.get('status')
    if status:
        transactions = transactions.filter(status=status)

    # Pagination
    paginator = Paginator(transactions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'transactions': page_obj,
        'query': query,
        'status': status,
    }
    return render(request, 'store/transaction_list.html', context)

@login_required
def transaction_create(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.branch = Profile.objects.get(user=request.user).branch
            transaction.requested_by = request.user
            transaction.status = 'PENDING'
            transaction.save()
            messages.success(request, 'Transaction created and pending approval.')
            return redirect('store:transaction_list')
    else:
        form = TransactionForm()
    return render(request, 'store/transaction_form.html', {'form': form, 'title': 'New Transaction'})

@login_required
def transaction_approve(request, pk):
    transaction = get_object_or_404(StockTransaction, pk=pk)
    if request.method == 'POST':
        transaction.status = 'APPROVED'
        transaction.approved_by = request.user
        
        # Update product quantity based on transaction type
        product = transaction.product
        if transaction.transaction_type == 'RECEIVE':
            product.quantity += transaction.quantity
        elif transaction.transaction_type == 'ISSUE':
            product.quantity -= transaction.quantity
        # For TRANSFER or ADJUST, you can add custom logic
        product.save()
        
        transaction.save()
        messages.success(request, f'Transaction approved! Stock updated.')
        return redirect('store:transaction_list')
    return render(request, 'store/transaction_approve.html', {'transaction': transaction})

@login_required
def transaction_edit(request, pk):
    transaction = get_object_or_404(StockTransaction, pk=pk)
    if transaction.status != 'PENDING':
        messages.warning(request, 'Only pending transactions can be edited.')
        return redirect('store:transaction_list')
    
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction updated.')
            return redirect('store:transaction_list')
    else:
        form = TransactionForm(instance=transaction)
    return render(request, 'store/transaction_form.html', {'form': form, 'title': 'Edit Transaction'})

@login_required
def transaction_delete(request, pk):
    transaction = get_object_or_404(StockTransaction, pk=pk)
    if transaction.status != 'PENDING':
        messages.warning(request, 'Only pending transactions can be deleted.')
        return redirect('store:transaction_list')
    
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Transaction deleted.')
        return redirect('store:transaction_list')
    return render(request, 'store/transaction_confirm_delete.html', {'transaction': transaction})


@login_required
def supplier_list(request):
    suppliers = Supplier.objects.all().order_by('company_name')
    return render(request, 'store/supplier_list.html', {'suppliers': suppliers})

@login_required
def supplier_create(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier added.')
            return redirect('store:supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'store/supplier_form.html', {'form': form, 'title': 'Add Supplier'})

@login_required
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier updated.')
            return redirect('store:supplier_list')
    else:
        form = SupplierForm(instance=supplier)
    return render(request, 'store/supplier_form.html', {'form': form, 'title': 'Edit Supplier'})

@login_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.delete()
        messages.success(request, 'Supplier deleted.')
        return redirect('store:supplier_list')
    return render(request, 'store/supplier_confirm_delete.html', {'supplier': supplier})



@login_required
def category_list(request):
    categories = Category.objects.all().order_by('name')
    return render(request, 'store/category_list.html', {'categories': categories})

@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added.')
            return redirect('store:category_list')
    else:
        form = CategoryForm()
    return render(request, 'store/category_form.html', {'form': form, 'title': 'Add Category'})

@login_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated.')
            return redirect('store:category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'store/category_form.html', {'form': form, 'title': 'Edit Category'})

@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted.')
        return redirect('store:category_list')
    return render(request, 'store/category_confirm_delete.html', {'category': category})




# ---------- SUPPLIER CRUD ----------
@login_required
def supplier_list(request):
    """List all suppliers."""
    # Superuser sees all, regular users see suppliers for their branch (if branch field exists)
    user = request.user
    if user.is_superuser:
        suppliers = Supplier.objects.all().order_by('company_name')
    else:
        # If Supplier has a branch field, filter by user's branch.
        # Currently Supplier model does NOT have branch, so show all.
        # You can add branch later if needed.
        suppliers = Supplier.objects.all().order_by('company_name')
    
    return render(request, 'store/supplier_list.html', {'suppliers': suppliers})


@login_required
@permission_required('store.add_supplier', raise_exception=True)
def supplier_create(request):
    """Create a new supplier."""
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            # If you add branch field, assign it here:
            # supplier.branch = Profile.objects.get(user=request.user).branch
            # supplier.created_by = request.user
            supplier.save()
            messages.success(request, f'Supplier "{supplier.company_name}" added successfully.')
            return redirect('store:supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'store/supplier_form.html', {'form': form, 'title': 'Add Supplier'})


@login_required
@permission_required('store.change_supplier', raise_exception=True)
def supplier_edit(request, pk):
    """Edit an existing supplier."""
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, f'Supplier "{supplier.company_name}" updated successfully.')
            return redirect('store:supplier_list')
    else:
        form = SupplierForm(instance=supplier)
    return render(request, 'store/supplier_form.html', {'form': form, 'title': 'Edit Supplier'})


@login_required
@permission_required('store.delete_supplier', raise_exception=True)
def supplier_delete(request, pk):
    """Delete a supplier."""
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.delete()
        messages.success(request, f'Supplier "{supplier.company_name}" deleted successfully.')
        return redirect('store:supplier_list')
    return render(request, 'store/supplier_confirm_delete.html', {'supplier': supplier})


# ---------- Products Report ----------
@login_required
@permission_required('store.view_product', raise_exception=True)
def products_report(request):
    user = request.user
    profile = user.profile
    queryset = Product.objects.select_related('category', 'supplier')
    if not user.is_superuser and profile.role != 'MAIN_ADMIN':
        queryset = queryset.filter(branch=profile.branch)

    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(item_code__icontains=search) |
            Q(category__name__icontains=search)
        )

    category_id = request.GET.get('category')
    if category_id:
        queryset = queryset.filter(category_id=category_id)

    supplier_id = request.GET.get('supplier')
    if supplier_id:
        queryset = queryset.filter(supplier_id=supplier_id)

    low_stock = request.GET.get('low_stock')
    if low_stock == 'yes':
        queryset = queryset.filter(quantity__lte=F('minimum_stock_level'))

    # Sort – only allow valid fields
    sort = request.GET.get('sort', 'name')
    allowed_sorts = ['name', 'quantity', 'minimum_stock_level']  # you can add 'category__name' or 'supplier__company_name' if desired
    if sort not in allowed_sorts:
        sort = 'name'
    queryset = queryset.order_by(sort)

    paginator = Paginator(queryset, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search': search,
        'category_id': category_id,
        'supplier_id': supplier_id,
        'low_stock': low_stock,
        'sort': sort,
        'categories': Category.objects.all(),
        'suppliers': Supplier.objects.all(),
    }
    return render(request, 'store/products_report.html', context)


# ---------- Low Stock Report ----------
@login_required
@permission_required('store.view_product', raise_exception=True)
def low_stock_report(request):
    user = request.user
    profile = user.profile
    queryset = Product.objects.select_related('category', 'supplier').filter(quantity__lte=F('minimum_stock_level'))
    if not user.is_superuser and profile.role != 'MAIN_ADMIN':
        queryset = queryset.filter(branch=profile.branch)

    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(item_code__icontains=search) |
            Q(category__name__icontains=search)
        )

    paginator = Paginator(queryset, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search': search,
        'total_low_stock': queryset.count(),
    }
    return render(request, 'store/low_stock_report.html', context)


# ---------- Stock Movement Report ----------
@login_required
@permission_required('store.view_stocktransaction', raise_exception=True)
def stock_movement_report(request):
    user = request.user
    profile = user.profile
    queryset = StockTransaction.objects.select_related('product', 'department', 'requested_by', 'approved_by')
    if not user.is_superuser and profile.role != 'MAIN_ADMIN':
        queryset = queryset.filter(branch=profile.branch)

    # Date range filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        queryset = queryset.filter(transaction_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(transaction_date__lte=end_date)

    # Transaction type filter
    txn_type = request.GET.get('txn_type')
    if txn_type:
        queryset = queryset.filter(transaction_type=txn_type)

    # Status filter
    status = request.GET.get('status')
    if status:
        queryset = queryset.filter(status=status)

    # Search by product name
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(product__name__icontains=search)

    queryset = queryset.order_by('-transaction_date')

    paginator = Paginator(queryset, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'start_date': start_date,
        'end_date': end_date,
        'txn_type': txn_type,
        'status': status,
        'search': search,
        'transaction_types': StockTransaction.TRANSACTION_TYPES,
        'status_choices': StockTransaction.STATUS_CHOICES,
    }
    return render(request, 'store/stock_movement_report.html', context)


# ---------- Stock In Report (only RECEIVE transactions) ----------
@login_required
@permission_required('store.view_stocktransaction', raise_exception=True)
def stock_in_report(request):
    user = request.user
    profile = user.profile
    queryset = StockTransaction.objects.filter(transaction_type='RECEIVE').select_related('product')
    if not user.is_superuser and profile.role != 'MAIN_ADMIN':
        queryset = queryset.filter(branch=profile.branch)

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        queryset = queryset.filter(transaction_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(transaction_date__lte=end_date)

    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(product__name__icontains=search)

    queryset = queryset.order_by('-transaction_date')

    paginator = Paginator(queryset, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'start_date': start_date,
        'end_date': end_date,
        'search': search,
        'total_quantity': queryset.aggregate(total=Sum('quantity'))['total'] or 0,
        # Removed total_value
    }
    return render(request, 'store/stock_in_report.html', context)


# ---------- Stock Out Report (ISSUE transactions only) ----------
@login_required
@permission_required('store.view_stocktransaction', raise_exception=True)
def stock_out_report(request):
    user = request.user
    profile = user.profile
    queryset = StockTransaction.objects.filter(transaction_type='ISSUE').select_related('product', 'department')
    if not user.is_superuser and profile.role != 'MAIN_ADMIN':
        queryset = queryset.filter(branch=profile.branch)

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        queryset = queryset.filter(transaction_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(transaction_date__lte=end_date)

    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(product__name__icontains=search)

    queryset = queryset.order_by('-transaction_date')

    paginator = Paginator(queryset, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'start_date': start_date,
        'end_date': end_date,
        'search': search,
        'total_quantity': queryset.aggregate(total=Sum('quantity'))['total'] or 0,
    }
    return render(request, 'store/stock_out_report.html', context)


# ---------- Department Consumption Report ----------
@login_required
@permission_required('store.view_stocktransaction', raise_exception=True)
def department_consumption_report(request):
    user = request.user
    profile = user.profile
    transactions = StockTransaction.objects.filter(transaction_type='ISSUE', status='APPROVED')
    if not user.is_superuser and profile.role != 'MAIN_ADMIN':
        transactions = transactions.filter(branch=profile.branch)

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        transactions = transactions.filter(transaction_date__gte=start_date)
    if end_date:
        transactions = transactions.filter(transaction_date__lte=end_date)

    consumption = transactions.values('department__name').annotate(
        total_quantity=Sum('quantity')
        # removed total_value
    ).order_by('-total_quantity')

    paginator = Paginator(consumption, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'start_date': start_date,
        'end_date': end_date,
        'grand_total_quantity': consumption.aggregate(total=Sum('total_quantity'))['total'] or 0,
    }
    return render(request, 'store/department_consumption_report.html', context)


#store/views.py
@login_required
@permission_required('store.view_supplier', raise_exception=True)
def supplier_report(request):
    user = request.user
    profile = user.profile
    queryset = Supplier.objects.prefetch_related('product_set')
    if not user.is_superuser and profile.role != 'MAIN_ADMIN':
        queryset = queryset.filter(branch=profile.branch)

    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(company_name__icontains=search) |
            Q(contact_person__icontains=search) |
            Q(phone__icontains=search)
        )

    # ✅ Annotate only product count – no value calculation
    queryset = queryset.annotate(product_count=Count('product')).order_by('-product_count')

    paginator = Paginator(queryset, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search': search,
    }
    return render(request, 'store/supplier_report.html', context)