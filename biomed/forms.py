# biomed/forms.py
from django import forms
from .models import Equipment, PPM, EquipmentStockTake, CorrectiveMaintenance
from .models import EquipmentTransfer
from user.models import Branch, Profile 
from .models import BiomedCategory


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        # FIXED: Use 'category' (not 'Biomedcategory')
        fields = [
            'equipment_name',
            'category',           # <-- CORRECT field name
            'manufacturer',
            'model_number',
            'serial_number',
            'asset_tag',
            'purchase_date',
            'purchase_cost',
            'supplier',
            'warranty_expiry',
            'department',
            'location',
            'status'
        ]
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'warranty_expiry': forms.DateInput(attrs={'type': 'date'}),
        }


class PPMForm(forms.ModelForm):
    serial_number = forms.CharField(required=False, disabled=True, widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}))
    model_number = forms.CharField(required=False, disabled=True, widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}))
    location = forms.CharField(required=False, disabled=True, widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}))

    class Meta:
        model = PPM
        fields = ['equipment', 'serial_number', 'model_number', 'location', 'ppm_date', 'next_ppm_date', 'technician', 'status', 'remarks']
        widgets = {
            'ppm_date': forms.DateInput(attrs={'type': 'date'}),
            'next_ppm_date': forms.DateInput(attrs={'type': 'date'}),
        }


class StockTakeForm(forms.ModelForm):
    class Meta:
        model = EquipmentStockTake
        fields = ['equipment', 'condition', 'remarks']


class EquipmentTransferForm(forms.ModelForm):
    class Meta:
        model = EquipmentTransfer
        fields = ['equipment', 'to_branch', 'remarks']
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            branch = Profile.objects.get(user=user).branch
            self.fields['equipment'].queryset = Equipment.objects.filter(branch=branch)
            self.fields['to_branch'].queryset = Branch.objects.exclude(id=branch.id)


class BiomedCategoryForm(forms.ModelForm):
    class Meta:
        model = BiomedCategory
        fields = ['name', 'description']


class CorrectiveMaintenanceForm(forms.ModelForm):
    class Meta:
        model = CorrectiveMaintenance
        fields = ['equipment', 'date', 'diagnosis', 'solution', 'remarks']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'diagnosis': forms.Textarea(attrs={'rows': 4}),
            'solution': forms.Textarea(attrs={'rows': 4}),
            'remarks': forms.Textarea(attrs={'rows': 3}),
        }
