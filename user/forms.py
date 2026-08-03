# user/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, Branch, Department, ROLE_CHOICES


ROLE_GROUP_NAMES = {
    'MAIN_ADMIN': 'Main Admin',
    'BRANCH_ADMIN': 'Branch Admin',
    'STORE_ADMIN': 'Store Admin',
    'STORE_OFFICER': 'Store Officer',
    'BIOMED_ADMIN': 'Biomed Admin',
    'BIOMED_TECHNICIAN': 'Biomed Technician',
}


def get_group_name_for_role(role):
    return ROLE_GROUP_NAMES.get(role, role)


class CreateUserForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(max_length=20, required=False)
    address = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., P.O. Box 123'}), required=False, max_length=100)
    branch = forms.ModelChoiceField(queryset=Branch.objects.filter(status=True), required=True)
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False)
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2',
                  'branch', 'department', 'role', 'phone', 'address']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show all departments by default so the dropdown is visible.
        self.fields['department'].queryset = Department.objects.all()

        # Dynamically filter departments based on selected branch (if provided)
        if 'branch' in self.data:
            try:
                branch_id = int(self.data.get('branch'))
                self.fields['department'].queryset = Department.objects.filter(branch_id=branch_id)
            except (ValueError, TypeError):
                pass

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            # Create or update profile
            profile, created = Profile.objects.get_or_create(user=user)
            profile.branch = self.cleaned_data['branch']
            profile.department = self.cleaned_data['department']
            profile.role = self.cleaned_data['role']
            profile.status = False
            profile.phone = self.cleaned_data.get('phone', '')
            profile.address = self.cleaned_data.get('address', '')
            profile.save()
            # Assign user to appropriate group
            from django.contrib.auth.models import Group
            group, _ = Group.objects.get_or_create(name=self.cleaned_data['role'])
            user.groups.add(group)
        return user


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']


class ProfileUpdateForm(forms.ModelForm):
    branch_logo = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        help_text='Upload the hospital/branch logo to use on reports and registration.',
    )
    branch = forms.ModelChoiceField(queryset=Branch.objects.filter(status=True), required=False)
    department = forms.ModelChoiceField(queryset=Department.objects.none(), required=False)
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=False)
    phone = forms.CharField(max_length=20, required=False)
    address = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=False, max_length=100)

    class Meta:
        model = Profile
        fields = ['phone', 'address', 'image', 'branch', 'department', 'role']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            if not (user.is_superuser or user.profile.role == 'MAIN_ADMIN'):
                self.fields['branch'].disabled = True
                self.fields['department'].disabled = True
                self.fields['role'].disabled = True
            if self.instance and not self.instance.branch:
                self.fields['branch_logo'].disabled = True
            # Filter department based on selected branch
            if 'branch' in self.data:
                try:
                    branch_id = int(self.data.get('branch'))
                    self.fields['department'].queryset = Department.objects.filter(branch_id=branch_id)
                except (ValueError, TypeError):
                    pass
            elif self.instance and self.instance.branch:
                self.fields['department'].queryset = Department.objects.filter(branch=self.instance.branch)
            else:
                self.fields['department'].queryset = Department.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        branch = cleaned_data.get('branch')
        department = cleaned_data.get('department')
        if branch and department and department.branch != branch:
            raise forms.ValidationError('Department does not belong to the selected branch.')
        return cleaned_data

    def save(self, commit=True):
        profile = super().save(commit=False)
        branch_logo = self.cleaned_data.get('branch_logo')
        if branch_logo and profile.branch:
            profile.branch.logo = branch_logo
            profile.branch.save()
        if commit:
            profile.save()
        return profile