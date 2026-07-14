# store/models.py
from django.db import models
from django.contrib.auth.models import User
from user.models import Branch, Department, Profile
from django.utils import timezone

CATEGORY_CHOICES = (
    ('Stationery', 'Stationery'),
    ('Kitchen', 'Kitchen'),
    ('Cleaning', 'Cleaning'),
    ('Uniforms', 'Uniforms'),
    ('Office Supplies', 'Office Supplies'),
    ('Medical Consumables', 'Medical Consumables'),
    ('PAIR', 'Pair'),
    ('PACKET', 'Packet'),
    ('DOZEN', 'Dozen'),
    ('CARTON', 'Carton'),
    ('BOTTLE', 'Bottle'),
    ('KG', 'Kilogram'),
    ('LITRE', 'Litre'),
    ('REAM', 'Ream'),
    ('PIECE', 'Piece'),
    ('BOX', 'Box'),
    ('Other', 'Other'),
)

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    # New fields for branch awareness
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Supplier(models.Model):
    company_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50)
    name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    # New fields for branch awareness
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name

class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    description = models.TextField(blank=True)
    item_code = models.CharField(max_length=50, unique=True, blank=True)
    unit = models.CharField(max_length=20, default='piece')
    quantity = models.PositiveIntegerField(default=0)
    minimum_stock_level = models.PositiveIntegerField(default=5)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    storage_location = models.CharField(max_length=100, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.quantity <= self.minimum_stock_level

class StockTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('RECEIVE', 'Receive from Supplier'),
        ('ISSUE', 'Issue to Department'),
        ('TRANSFER', 'Transfer between Branches'),
        ('ADJUST', 'Stock Adjustment'),
    )
    STATUS_CHOICES = (
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='requested_transactions')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_transactions')
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='issued_transactions')
    transaction_date = models.DateTimeField(default=timezone.now)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.product.name} ({self.quantity})"
    
    

