# dashboard/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, F, Sum
from django.utils import timezone
from datetime import timedelta
import json

from store.models import Product, StockTransaction, Category
from biomed.models import Equipment, PPM, EquipmentTransfer
from user.models import Branch, Department
from django.contrib.auth.models import User


@login_required(login_url='user:login')
def index(request):
    user = request.user
    profile = user.profile
    now = timezone.now()

    # ---------- Default chart_data ----------
    chart_data = {
        'equipment_labels': [],
        'equipment_data': [],
        'month_labels': [],
        'month_counts': [],
        'low_stock_labels': [],
        'low_stock_qty': [],
        'low_stock_min': [],
        'category_labels': [],
        'category_data': [],
        'low_labels': [],
        'stock_qty': [],
        'min_qty': [],
        'eq_labels': [],
        'eq_data': [],
        'ppm_labels': [],
        'ppm_data': [],
        'movement_months': [],
        'received_qty': [],
        'issued_qty': [],
        'dept_labels': [],
        'dept_data': [],
    }

    # ---------- Common context ----------
    context = {
        'user_role': profile.role,
        'branch': profile.branch,
        'total_branches': Branch.objects.filter(status=True).count(),
        'total_products': Product.objects.count(),
        'total_equipment': Equipment.objects.count(),
        'chart_data': chart_data,
        'now': now,
        'greeting': f"Welcome back, {user.get_full_name() or user.username}!",
    }

    # ---------- MAIN ADMIN / SUPERUSER ----------
    if user.is_superuser or profile.role == 'MAIN_ADMIN':
        pending_transactions = StockTransaction.objects.filter(status='PENDING').count()
        pending_transfers = EquipmentTransfer.objects.filter(status='PENDING').count()
        low_stock_count = Product.objects.filter(quantity__lte=F('minimum_stock_level')).count()
        upcoming_ppm_count = PPM.objects.filter(
            status__in=['Pending', 'Overdue'],
            ppm_date__gte=timezone.now().date()
        ).count()
        overdue_ppm_count = PPM.objects.filter(status='Overdue').count()
        total_transactions = StockTransaction.objects.count()
         # Inside the MAIN_ADMIN block:
        stock_in_count = StockTransaction.objects.filter(transaction_type='RECEIVE').count()
        stock_out_count = StockTransaction.objects.filter(transaction_type='ISSUE').count()
        # Then add to context.update():
            
        # ---- BIOMED STATS FOR MAIN ADMIN ----
        total_equipment = Equipment.objects.count()
        working_count = Equipment.objects.filter(status='Working').count()
        faulty_count = Equipment.objects.filter(status='Not Working').count()
        under_repair_count = Equipment.objects.filter(status='Under Repair').count()

        context.update({
            'show_main_admin': True,
            'total_transactions': total_transactions,
            'total_equipment': total_equipment,
            'working_count': working_count,
            'faulty_count': faulty_count,
            'under_repair_count': under_repair_count,
            'pending_approvals': pending_transactions + pending_transfers,
            'low_stock_count': low_stock_count,
            'upcoming_ppm_count': upcoming_ppm_count,
            'overdue_ppm_count': overdue_ppm_count,
            'pending_transactions': pending_transactions,
            'pending_transfers': pending_transfers,
            'recent_transactions': StockTransaction.objects.all().order_by('-transaction_date')[:5],
            'recent_equipment': Equipment.objects.all().order_by('-date_added')[:5],
            
            'stock_in_count': stock_in_count,
            'stock_out_count': stock_out_count,
        })

        # ----- Equipment Status -----
        status_counts = Equipment.objects.values('status').annotate(count=Count('id'))
        chart_data['equipment_labels'] = json.dumps([item['status'] for item in status_counts])
        chart_data['equipment_data'] = json.dumps([item['count'] for item in status_counts])

        # ----- Monthly Transactions -----
        now_date = timezone.now().date()
        month_labels, month_counts = [], []
        for i in range(5, -1, -1):
            month_start = now_date - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            count = StockTransaction.objects.filter(
                transaction_date__gte=month_start,
                transaction_date__lt=month_end
            ).count()
            month_labels.append(month_start.strftime('%b %Y'))
            month_counts.append(count)
        chart_data['month_labels'] = json.dumps(month_labels)
        chart_data['month_counts'] = json.dumps(month_counts)

        # ----- Low Stock Products (Top 5) -----
        low_products = Product.objects.filter(quantity__lte=F('minimum_stock_level')).order_by('quantity')[:5]
        chart_data['low_stock_labels'] = json.dumps([p.name for p in low_products])
        chart_data['low_stock_qty'] = json.dumps([p.quantity for p in low_products])
        chart_data['low_stock_min'] = json.dumps([p.minimum_stock_level for p in low_products])

        # ----- Stock Movement (Receive vs Issue) -----
        movement_months, received_qty, issued_qty = [], [], []
        for i in range(5, -1, -1):
            month_start = now_date - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            received = StockTransaction.objects.filter(
                transaction_type='RECEIVE',
                transaction_date__gte=month_start,
                transaction_date__lt=month_end
            ).aggregate(total=Sum('quantity'))['total'] or 0
            issued = StockTransaction.objects.filter(
                transaction_type='ISSUE',
                transaction_date__gte=month_start,
                transaction_date__lt=month_end
            ).aggregate(total=Sum('quantity'))['total'] or 0
            movement_months.append(month_start.strftime('%b %Y'))
            received_qty.append(received)
            issued_qty.append(issued)
        chart_data['movement_months'] = json.dumps(movement_months)
        chart_data['received_qty'] = json.dumps(received_qty)
        chart_data['issued_qty'] = json.dumps(issued_qty)

        # ----- Equipment by Department -----
        dept_counts = Equipment.objects.values('department__name').annotate(count=Count('id')).order_by('-count')
        dept_labels = [d['department__name'] or 'Unassigned' for d in dept_counts]
        dept_data = [d['count'] for d in dept_counts]
        chart_data['dept_labels'] = json.dumps(dept_labels)
        chart_data['dept_data'] = json.dumps(dept_data)

    # ---------- STORE ADMIN / OFFICER ----------
    elif profile.role in ['STORE_ADMIN', 'STORE_OFFICER']:
        branch = profile.branch
        products = Product.objects.filter(branch=branch)
        low_stock = products.filter(quantity__lte=F('minimum_stock_level'))
        pending_transactions = StockTransaction.objects.filter(branch=branch, status='PENDING')
        total_transactions = StockTransaction.objects.filter(branch=branch).count()

        context.update({
            'show_store': True,
            'product_count': products.count(),
            'low_stock_count': low_stock.count(),
            'total_transactions': total_transactions,
            'pending_transactions': pending_transactions.count(),
            'recent_transactions': StockTransaction.objects.filter(branch=branch).order_by('-transaction_date')[:5],
        })

        # Category distribution
        cat_counts = Category.objects.filter(product__branch=branch).annotate(count=Count('product'))
        chart_data['category_labels'] = json.dumps([c.name for c in cat_counts])
        chart_data['category_data'] = json.dumps([c.count for c in cat_counts])

        # Stock vs Min
        low_products = products.filter(quantity__lte=F('minimum_stock_level')).order_by('quantity')[:5]
        chart_data['low_labels'] = json.dumps([p.name for p in low_products])
        chart_data['stock_qty'] = json.dumps([p.quantity for p in low_products])
        chart_data['min_qty'] = json.dumps([p.minimum_stock_level for p in low_products])

    # ---------- BIOMED ADMIN / TECHNICIAN ----------
    elif profile.role in ['BIOMED_ADMIN', 'BIOMED_TECHNICIAN']:
        branch = profile.branch
        equipment = Equipment.objects.filter(branch=branch)
        working = equipment.filter(status='Working').count()
        faulty = equipment.filter(status='Not Working').count()
        under_repair = equipment.filter(status='Under Repair').count()
        pending_ppm = PPM.objects.filter(equipment__branch=branch, status='Pending').count()
        overdue_ppm = PPM.objects.filter(equipment__branch=branch, status='Overdue').count()
        pending_transfers = EquipmentTransfer.objects.filter(
            Q(from_branch=branch) | Q(to_branch=branch),
            status='PENDING'
        ).count()

        context.update({
            'show_biomed': True,
            'total_equipment': equipment.count(),
            'working_count': working,
            'faulty_count': faulty,
            'under_repair_count': under_repair,
            'pending_ppm': pending_ppm,
            'overdue_ppm': overdue_ppm,
            'pending_transfers': pending_transfers,
            'recent_ppm': PPM.objects.filter(equipment__branch=branch).order_by('-ppm_date')[:5],
        })

        # Equipment status
        status_counts = equipment.values('status').annotate(count=Count('id'))
        chart_data['eq_labels'] = json.dumps([item['status'] for item in status_counts])
        chart_data['eq_data'] = json.dumps([item['count'] for item in status_counts])

        # PPM status
        ppm_status = PPM.objects.filter(equipment__branch=branch).values('status').annotate(count=Count('id'))
        chart_data['ppm_labels'] = json.dumps([s['status'] for s in ppm_status])
        chart_data['ppm_data'] = json.dumps([s['count'] for s in ppm_status])

    # ---------- BRANCH ADMIN ----------
    elif profile.role == 'BRANCH_ADMIN':
        branch = profile.branch
        products = Product.objects.filter(branch=branch)
        low_stock = products.filter(quantity__lte=F('minimum_stock_level'))
        pending_transactions = StockTransaction.objects.filter(branch=branch, status='PENDING')
        equipment = Equipment.objects.filter(branch=branch)
        working = equipment.filter(status='Working').count()
        faulty = equipment.filter(status='Not Working').count()
        under_repair = equipment.filter(status='Under Repair').count()
        pending_ppm = PPM.objects.filter(equipment__branch=branch, status='Pending').count()
        overdue_ppm = PPM.objects.filter(equipment__branch=branch, status='Overdue').count()
        pending_transfers = EquipmentTransfer.objects.filter(
            Q(from_branch=branch) | Q(to_branch=branch),
            status='PENDING'
        ).count()
        total_transactions = StockTransaction.objects.filter(branch=branch).count()

        context.update({
            'show_branch_admin': True,
            'product_count': products.count(),
            'low_stock_count': low_stock.count(),
            'total_transactions': total_transactions,
            'pending_transactions': pending_transactions.count(),
            'recent_transactions': StockTransaction.objects.filter(branch=branch).order_by('-transaction_date')[:5],
            'total_equipment': equipment.count(),
            'working_count': working,
            'faulty_count': faulty,
            'under_repair_count': under_repair,
            'pending_ppm': pending_ppm,
            'overdue_ppm': overdue_ppm,
            'pending_transfers': pending_transfers,
            'recent_ppm': PPM.objects.filter(equipment__branch=branch).order_by('-ppm_date')[:5],
        })

        # Equipment status
        status_counts = equipment.values('status').annotate(count=Count('id'))
        chart_data['eq_labels'] = json.dumps([item['status'] for item in status_counts])
        chart_data['eq_data'] = json.dumps([item['count'] for item in status_counts])

        # Stock vs Min
        low_products = products.filter(quantity__lte=F('minimum_stock_level')).order_by('quantity')[:5]
        chart_data['low_labels'] = json.dumps([p.name for p in low_products])
        chart_data['stock_qty'] = json.dumps([p.quantity for p in low_products])
        chart_data['min_qty'] = json.dumps([p.minimum_stock_level for p in low_products])

    # ---------- Fallback ----------
    else:
        context['message'] = 'Welcome to Eagle Hospital IMS. Please contact admin for access.'
        # Force show basic data for debugging
        context['show_main_admin'] = True
        context['total_products'] = Product.objects.count()
        context['low_stock_count'] = Product.objects.filter(quantity__lte=F('minimum_stock_level')).count()
        context['pending_transactions'] = StockTransaction.objects.filter(status='PENDING').count()
        context['total_equipment'] = Equipment.objects.count()
        context['working_count'] = Equipment.objects.filter(status='Working').count()
        context['faulty_count'] = Equipment.objects.filter(status='Not Working').count()
        context['under_repair_count'] = Equipment.objects.filter(status='Under Repair').count()

    # ---------- Quick Actions ----------
    context['can_add_product'] = user.has_perm('store.add_product')
    context['can_add_transaction'] = user.has_perm('store.add_stocktransaction')
    context['can_add_equipment'] = user.has_perm('biomed.add_equipment')
    context['can_add_ppm'] = user.has_perm('biomed.add_ppm')

    # Pass chart_data as JSON
    context['chart_data_json'] = json.dumps(chart_data)
    context['chart_data'] = chart_data

    # ========== DEBUG ==========
    print("📍 Rendering dashboard/index.html")
    print(f"🔍 user: {user.username}, role: {profile.role}")
    print(f"📊 show_main_admin: {context.get('show_main_admin')}")
    print(f"📊 show_store: {context.get('show_store')}")
    print(f"📊 show_biomed: {context.get('show_biomed')}")
    print(f"📊 show_branch_admin: {context.get('show_branch_admin')}")
    # ============================

    return render(request, 'dashboard/main.html',context)


