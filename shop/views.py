import os
import random
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.views.decorators.http import require_POST
from django.core.cache import cache
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from .models import Product, Category, Order, OrderItem, UserProfile
from .forms import UserSettingsForm, ProductCreateForm, CustomerRegistrationForm
from .cart import Cart

FLASK_PDF_SERVICE_URL = os.getenv('FLASK_PDF_SERVICE_URL', 'http://127.0.0.1:8002')


# ==========================================
# 🏠 HOME PAGE CONTROLLER
# ==========================================

def home_page(request):
    categories = cache.get('global_store_categories')
    if not categories:
        categories = Category.objects.all()
        cache.set('global_store_categories', categories, 60 * 15)

    hero_product = Product.objects.filter(is_sold=False).select_related('category').order_by('-id').first()

    laptop_promo = Product.objects.filter(
        is_sold=False,
        category__name__icontains='laptop'
    ).select_related('category').order_by('-id').first()

    tablet_promo = Product.objects.filter(
        is_sold=False,
        category__name__icontains='tablet'
    ).select_related('category').order_by('-id').first()

    phones_top_picks = Product.objects.filter(
        is_sold=False
    ).filter(
        Q(category__slug__icontains='phone') | Q(category__name__icontains='phone') | Q(category__name__icontains='mobile')
    ).select_related('category').order_by('-id')[:5]

    laptops_top_picks = Product.objects.filter(
        is_sold=False
    ).filter(
        Q(category__slug__icontains='laptop') | Q(category__name__icontains='laptop')
    ).select_related('category').order_by('-id')[:5]

    tablets_top_picks = Product.objects.filter(
        is_sold=False
    ).filter(
        Q(category__slug__icontains='tablet') | Q(category__name__icontains='tablet') | Q(category__name__icontains='ipad') | Q(category__name__icontains='pad')
    ).select_related('category').order_by('-id')[:5]

    context = {
        'categories': categories,
        'hero_product': hero_product,
        'laptop_promo': laptop_promo,
        'tablet_promo': tablet_promo,
        'phones_top_picks': phones_top_picks,
        'laptops_top_picks': laptops_top_picks,
        'tablets_top_picks': tablets_top_picks,
    }
    return render(request, 'shop/home.html', context)


# ==========================================
# 🏪 CATALOG CONTROLLERS
# ==========================================

def product_list(request, category_slug=None):
    category = None
    categories = cache.get('global_store_categories')
    if not categories:
        categories = Category.objects.all()
        cache.set('global_store_categories', categories, 60 * 15)

    products_list = Product.objects.filter(is_sold=False).select_related('category').order_by('-id')
    type_filter = request.GET.get('type') or category_slug

    if type_filter == 'phones':
        type_filter = 'phone'
    elif type_filter == 'laptops':
        type_filter = 'laptop'
    elif type_filter == 'tablets':
        type_filter = 'tablet'

    brand_filter = request.GET.get('brand')
    search_query = request.GET.get('search')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    has_active_filters = bool(type_filter or brand_filter or search_query or min_price or max_price)

    if type_filter:
        products_list = products_list.filter(
            Q(category__slug__iexact=type_filter) | Q(category__name__icontains=type_filter)
        )

    if brand_filter:
        products_list = products_list.filter(brand__iexact=brand_filter)

    if search_query:
        products_list = products_list.filter(
            Q(name__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if min_price:
        try:
            products_list = products_list.filter(price__gte=float(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            products_list = products_list.filter(price__lte=float(max_price))
        except ValueError:
            pass

    available_brands = Product.objects.filter(is_sold=False).values_list('brand', flat=True).distinct()

    paginator = Paginator(products_list.distinct(), 15)
    page_number = request.GET.get('page')

    try:
        products = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        products = paginator.page(1)

    grouped_sections = {}
    if not has_active_filters:
        grouped_sections = {
            'phones': Product.objects.filter(is_sold=False, category__name__icontains='phone').select_related('category').order_by('-id')[:5],
            'laptops': Product.objects.filter(is_sold=False, category__name__icontains='laptop').select_related('category').order_by('-id')[:5],
            'tablets': Product.objects.filter(is_sold=False, category__name__icontains='tablet').select_related('category').order_by('-id')[:5],
        }

    context = {
        'category': category,
        'categories': categories,
        'products': products,
        'available_brands': available_brands,
        'selected_type': type_filter or '',
        'selected_brand': brand_filter or '',
        'min_price': min_price or '',
        'max_price': max_price or '',
        'search_query': search_query or '',
        'has_active_filters': has_active_filters,
        'grouped_sections': grouped_sections,
    }
    return render(request, 'shop/product/list.html', context)


def product_detail(request, product_slug):
    product = get_object_or_404(Product.objects.select_related('category'), slug=product_slug, is_sold=False)
    return render(request, 'shop/product/detail.html', {'product': product})


def product_specs(request, product_slug):
    product = get_object_or_404(Product.objects.select_related('category'), slug=product_slug, is_sold=False)
    return render(request, 'shop/product/specs.html', {'product': product})


# ==========================================
# 🔐 AUTHENTICATION & CUSTOMER REGISTRATION
# ==========================================

def register_customer(request):
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.email = form.cleaned_data.get('email', '')
            user.save()

            method = form.cleaned_data['verification_method']
            otp_code = str(random.randint(100000, 999999))

            profile = UserProfile.objects.create(
                user=user,
                passport_number=form.cleaned_data['passport_number'],
                verification_method=method,
                phone_number=form.cleaned_data.get('phone_number', '')
            )

            if method == 'email':
                profile.email_otp = otp_code
                profile.save()
                send_mail(
                    subject='TechVault Verification Code',
                    message=f'Your activation code is: {otp_code}',
                    from_email='noreply@techvault.com',
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            else:
                profile.phone_otp = otp_code
                profile.save()
                # SMS integration placeholder

            login(request, user)
            messages.info(request, f"Please verify your code sent via {method}.")
            return redirect('shop:verify_otp')
        else:
            messages.error(request, "Please correct the registration errors below.")
    else:
        form = CustomerRegistrationForm()

    return render(request, 'shop/auth/register.html', {'form': form})


@login_required
def verify_otp(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        entered_code = request.POST.get('otp_code', '').strip()

        if profile.verification_method == 'email' and entered_code == profile.email_otp:
            profile.is_email_verified = True
            profile.kyc_status = 'verified'
            profile.save()
            messages.success(request, "Email verified successfully! Account fully activated.")
            return redirect('shop:home')
        elif profile.verification_method == 'phone' and entered_code == profile.phone_otp:
            profile.is_phone_verified = True
            profile.kyc_status = 'verified'
            profile.save()
            messages.success(request, "Phone verified successfully! Account fully activated.")
            return redirect('shop:home')
        else:
            messages.error(request, "Invalid verification code. Please check and try again.")

    return render(request, 'shop/auth/verify_otp.html', {'profile': profile})


def login_customer(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name}!")
            return redirect('shop:home')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'shop/auth/login.html', {'form': form})


def logout_customer(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('shop:home')


# ==========================================
# 🛒 SHOPPING CART SYSTEM MANAGEMENT
# ==========================================

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_sold=False)

    added = cart.add(product=product, quantity=1)
    if added:
        messages.success(request, f"{product.name} added to cart!")
    else:
        messages.warning(request, f"{product.name} is already in your cart!")

    return redirect('shop:cart_detail')


def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('shop:cart_detail')


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'shop/cart/detail.html', {'cart': cart})


# ==========================================
# 💎 PROFILE SETTINGS
# ==========================================

@login_required
def account_settings(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserSettingsForm(request.POST, request.FILES, instance=request.user, profile_instance=profile)
        if form.is_valid():
            updated_user = form.save()
            update_session_auth_hash(request, updated_user)
            messages.success(request, "Your account settings have been updated successfully.")
            return redirect('shop:account_settings')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserSettingsForm(instance=request.user, profile_instance=profile)

    return render(request, 'shop/auth/settings.html', {'form': form})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated!")
            return redirect('shop:account_settings')
        else:
            messages.error(request, "Please correct the errors down below.")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'shop/auth/change_password.html', {'form': form})


@login_required
def payment_method_settings(request):
    return render(request, 'shop/auth/payment_settings.html')


# ==========================================
# 🧾 CHECKOUT & ORDERS
# ==========================================

@login_required
def checkout_order(request):
    cart_session = request.session.get('techvault_cart', {})
    if not cart_session:
        messages.error(request, "Your cart is empty.")
        return redirect('shop:product_list')

    product_id = list(cart_session.keys())[0]
    try:
        product = Product.objects.get(id=product_id, is_sold=False)
    except Product.DoesNotExist:
        messages.error(request, "This item is no longer available.")
        return redirect('shop:cart_detail')

    order = Order.objects.create(user=request.user, total_price=product.price)
    OrderItem.objects.create(order=order, product=product, price=product.price, quantity=1)

    product.is_sold = True
    product.save()

    request.session['techvault_cart'] = {}

    flask_endpoint = f"{FLASK_PDF_SERVICE_URL}/api/v1/generate-invoice"
    payload = {
        "order_id": str(order.id),
        "customer_name": f"{request.user.first_name} {request.user.last_name}" if request.user.first_name else request.user.username,
        "product_name": f"{product.brand} {product.name}",
        "price": str(product.price)
    }

    try:
        response = requests.post(flask_endpoint, json=payload, timeout=5)
        if response.status_code == 201:
            messages.success(request, f"Success! Order #{order.id} processed. Your background PDF receipt is ready!")
        else:
            messages.warning(request, f"Order #{order.id} processed, but background invoice worker returned status code {response.status_code}.")
    except requests.exceptions.RequestException:
        messages.warning(request, f"Order #{order.id} logged securely, but the PDF invoice microservice is currently offline.")

    return redirect('shop:product_list')


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/auth/order_history.html', {'orders': orders})


# ==========================================
# 📄 AUXILIARY PAGES
# ==========================================

def about_us(request):
    return render(request, 'shop/pages/about.html')


def contact_us(request):
    return render(request, 'shop/pages/contact.html')


def is_admin_or_manager(user):
    return user.is_authenticated and (
            user.is_staff or
            user.is_superuser or
            user.groups.filter(name__in=['Admins', 'Managers']).exists()
    )


@login_required
@user_passes_test(is_admin_or_manager, login_url='shop:product_list', redirect_field_name=None)
def create_product(request, product_id=None):
    product_instance = None
    if product_id:
        product_instance = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = ProductCreateForm(request.POST, request.FILES, instance=product_instance)
        if form.is_valid():
            form.save()
            action_text = "updated" if product_instance else "cataloged"
            messages.success(request, f"Product successfully {action_text}!")
            return redirect('shop:product_list')
        else:
            messages.error(request, "Please correct the entry errors down below.")
    else:
        form = ProductCreateForm(instance=product_instance)

    all_products = Product.objects.filter(is_sold=False).select_related('category').order_by('-id')

    context = {
        'form': form,
        'product_instance': product_instance,
        'all_products': all_products,
    }
    return render(request, 'shop/product/create.html', context)


@login_required
@user_passes_test(is_admin_or_manager, login_url='shop:product_list', redirect_field_name=None)
def admin_purchase_history(request):
    all_purchases = OrderItem.objects.select_related('order__user', 'product').order_by('-order__created_at')

    paginator = Paginator(all_purchases, 25)
    page_number = request.GET.get('page')
    try:
        purchases = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        purchases = paginator.page(1)

    context = {
        'purchases': purchases,
    }
    return render(request, 'shop/admin/purchase_history.html', context)