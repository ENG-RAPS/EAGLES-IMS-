# biomed/models.py
from django.db import models
from django.contrib.auth.models import User
from user.models import Branch, Department
from store.models import Supplier
from django.utils import timezone

# ============================================================
# 1. BIOMED CATEGORY (MUST BE DEFINED BEFORE Equipment)
# ============================================================
class BiomedCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='biomed_categories_created'
    )

    class Meta:
        verbose_name_plural = "Biomed Categories"

    def __str__(self):
        return self.name


# ============================================================
# 2. EQUIPMENT STATUS CHOICES
# ============================================================
EQUIPMENT_STATUS = (
    ('Working', 'Working'),
    ('Not Working', 'Not Working'),
    ('Under Repair', 'Under Repair'),
    ('Decommissioned', 'Decommissioned'),
)


# ============================================================
# 3. EQUIPMENT
# ============================================================
class Equipment(models.Model):
    equipment_name = models.CharField(max_length=200)
    category = models.ForeignKey(
        BiomedCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    manufacturer = models.CharField(max_length=100, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, unique=True, blank=True)
    asset_tag = models.CharField(max_length=100, unique=True, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    purchase_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    warranty_expiry = models.DateField(null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    location = models.CharField(max_length=200, blank=True)
    status = models.CharField(
        max_length=20,
        choices=EQUIPMENT_STATUS,
        default='Working'
    )
    date_added = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipment_created'
    )

    def __str__(self):
        return f"{self.equipment_name} ({self.serial_number or self.asset_tag or 'No ID'})"


# ============================================================
# 4. PPM (Preventive Maintenance)
# ============================================================
class PPM(models.Model):
    PPM_STATUS = (
        ('Completed', 'Completed'),
        ('Pending', 'Pending'),
        ('Overdue', 'Overdue'),
    )

    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    serial_number = models.CharField(max_length=100, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=200, blank=True)
    previous_ppm_date = models.DateField(null=True, blank=True)
    ppm_date = models.DateField()
    next_ppm_date = models.DateField()
    technician = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ppm_technician'
    )
    status = models.CharField(
        max_length=20,
        choices=PPM_STATUS,
        default='Pending'
    )
    remarks = models.TextField(blank=True)

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ppm_created'
    )

    def __str__(self):
        return f"PPM for {self.equipment.equipment_name} on {self.ppm_date}"


# ============================================================
# 5. EQUIPMENT STOCK TAKE
# ============================================================
class EquipmentStockTake(models.Model):
    CONDITION_CHOICES = (
        ('Good', 'Good'),
        ('Damaged', 'Damaged'),
        ('Missing', 'Missing'),
        ('Decommissioned', 'Decommissioned'),
    )

    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    remarks = models.TextField(blank=True)
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stocktake_performed'
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"StockTake {self.equipment.equipment_name} - {self.condition}"


# ============================================================
# 6. EQUIPMENT TRANSFER
# ============================================================
class EquipmentTransfer(models.Model):
    TRANSFER_STATUS = (
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    )

    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='transfers'
    )
    from_branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='equipment_transfers_from'
    )
    to_branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='equipment_transfers_to'
    )
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requested_equipment_transfers'
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_equipment_transfers'
    )
    transfer_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=20,
        choices=TRANSFER_STATUS,
        default='PENDING'
    )
    remarks = models.TextField(blank=True)

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = [
            
            ("approve_equipmenttransfer", "Can approve equipment transfer"),
        ]

    def __str__(self):
        return f"Transfer {self.equipment.equipment_name} from {self.from_branch.name} to {self.to_branch.name}"

    def approve(self, user):
        """Approve the transfer and update equipment branch."""
        if self.status == 'PENDING':
            self.status = 'APPROVED'
            self.approved_by = user
            # Update equipment branch to destination
            self.equipment.branch = self.to_branch
            self.equipment.save()
            self.save()
            return True
        return False

    def complete(self):
        """Mark as completed (optional)."""
        if self.status == 'APPROVED':
            self.status = 'COMPLETED'
            self.save()
            return True
        return False