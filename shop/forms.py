from django import forms
from django.contrib.auth.models import User
from django.utils.text import slugify
from .models import UserProfile, Product, Category


# ==========================================
# 👤 USER ACCOUNT & PROFILE SETTINGS FORM
# ==========================================

class UserSettingsForm(forms.ModelForm):
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-gray-50/50',
            'placeholder': '+996 555 123 456'
        })
    )

    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-gray-50/50',
                'placeholder': 'Your username'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-gray-50/50',
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-gray-50/50',
                'placeholder': 'Last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-gray-50/50',
                'placeholder': 'name@example.com'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.profile_instance = kwargs.pop('profile_instance', None)
        super().__init__(*args, **kwargs)
        if self.profile_instance:
            self.fields['phone_number'].initial = self.profile_instance.phone_number
            self.fields['profile_picture'].initial = self.profile_instance.profile_picture

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit and self.profile_instance:
            self.profile_instance.phone_number = self.cleaned_data['phone_number']
            if 'profile_picture' in self.changed_data:
                self.profile_instance.profile_picture = self.cleaned_data['profile_picture']
            self.profile_instance.save()
        return user


# ==========================================
# 📦 PRODUCT CREATION & UPDATE FORM
# ==========================================

class ProductCreateForm(forms.ModelForm):
    # Optional Slug Field (Auto-generates if left empty)
    slug = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-gray-50/50',
            'placeholder': 'Auto-generated if empty (e.g., iphone-15-pro-max)'
        })
    )

    # Structured Drop-down Fields for Specifications
    ram_option = forms.ChoiceField(
        choices=[('', '-- Select RAM --'), ('8GB', '8GB RAM'), ('12GB', '12GB RAM'), ('16GB', '16GB RAM'),
                 ('32GB', '32GB RAM')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-gray-50/50'})
    )
    storage_option = forms.ChoiceField(
        choices=[('', '-- Select Storage --'), ('128GB', '128GB Storage'), ('256GB', '256GB Storage'),
                 ('512GB', '512GB Storage'), ('1TB', '1TB Storage')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-gray-50/50'})
    )
    screen_option = forms.ChoiceField(
        choices=[('', '-- Select Screen Size --'), ('6.1 inch OLED', '6.1 inch OLED'),
                 ('6.7 inch OLED', '6.7 inch OLED'), ('14 inch Retina', '14 inch Retina'),
                 ('16 inch Retina', '16 inch Retina')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-gray-50/50'})
    )
    processor_option = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-gray-50/50',
            'placeholder': 'e.g., Apple A17 Pro, Snapdragon 8 Gen 3, Intel Core i7'
        })
    )

    class Meta:
        model = Product
        fields = ['category', 'brand', 'name', 'slug', 'price', 'image', 'ram_option', 'storage_option',
                  'screen_option', 'processor_option']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-gray-50/50'
            }),
            'brand': forms.TextInput(attrs={
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-gray-50/50',
                'placeholder': 'e.g., Apple, Samsung, ASUS'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-gray-50/50',
                'placeholder': 'e.g., iPhone 15 Pro Max'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-gray-50/50',
                'placeholder': '999.99'
            }),
            'image': forms.FileInput(attrs={
                'class': 'text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 cursor-pointer'
            }),
        }

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        name = self.cleaned_data.get('name')

        if not slug and name:
            slug = slugify(name)

        # 🔥 CRITICAL FIX: Exclude the current product ID when checking uniqueness during updates!
        qs = Product.objects.filter(slug=slug)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            slug = f"{slug}-{Product.objects.count() + 1}"

        return slug

    def save(self, commit=True):
        product = super().save(commit=False)

        ram = self.cleaned_data.get('ram_option')
        storage = self.cleaned_data.get('storage_option')
        screen = self.cleaned_data.get('screen_option')
        processor = self.cleaned_data.get('processor_option')

        specs = {}
        desc_parts = []

        if ram:
            specs['RAM'] = ram
            desc_parts.append(f"RAM: {ram}")
        if storage:
            specs['Storage'] = storage
            desc_parts.append(f"Storage: {storage}")
        if screen:
            specs['Screen'] = screen
            desc_parts.append(f"Screen: {screen}")
        if processor:
            specs['Processor'] = processor
            desc_parts.append(f"Processor: {processor}")

        # Only update specs/description if user selected new option values
        if specs:
            product.specifications = specs
            product.description = " | ".join(desc_parts)

        if commit:
            product.save()
        return product