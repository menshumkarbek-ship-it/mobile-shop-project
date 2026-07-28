import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.views.decorators.http import require_POST
from django.core.cache import cache  # 🏎️ Redis Core Caching Engine
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger  # 📏 Pagination Engine
from django.db.models import Q

# Explicit model and custom form components
from .models import Product, Category, Order, OrderItem, UserProfile
from .forms import UserSettingsForm, ProductCreateForm
from .cart import Cart


# ==========================================
# 🏠 HOME & LANDING PAGE CONTROLLER
# ==========================================

def home_page(request):
    """
    Renders the custom Home Page with:
    - 🔴 Automatic Top Pick Hero Item (Latest unsold flagship product)
    - 🟢 Latest Model per Brand in the Slideshow Dataset (Apple, Samsung, Xiaomi, etc.)
    """
    # 🏎️ Redis cached categories
    categories = cache.get('global_store_categories')
    if not categories:
        categories = Category.objects.all()
        cache.set('global_store_categories', categories, 60 * 15)

    # 🔴 Red Section: Automatic Top Pick Hero (Calculates the latest unsold product)
    hero_product = Product.objects.filter(is_sold=False).order_by('-id').first()

    # 🟢 Green Section: Distinct Top Model per Brand
    all_unsold = Product.objects.filter(is_sold=False).select_related('category').order_by('-created_at')

    # Group by brand to pick only the single newest device per brand
    latest_per_brand = {}
    for product in all_unsold:
        brand_key = product.brand.strip().title() if product.brand else "Generic"
        if brand_key not in latest_per_brand:
            latest_per_brand[brand_key] = product

    top_picks_by_brand = list(latest_per_brand.values())

    context = {
        'categories': categories,
        'hero_product': hero_product,
        'all_top_picks': top_picks_by_brand,
    }
    return render(request, 'shop/home.html', context)


# ==========================================
# 🏪 CATALOG & INVENTORY CONTROLLERS
# ==========================================

def product_list(request, category_slug=None):
    """
    Renders the catalog page:
    - Interactive top filter bar (Device Type, Brand, Price Range)
    - By default (no filters active): Renders separate rows for Phones, Laptops, Tablets (4 per row).
    - When filters active: Renders a paginated 4-column grid layout.
    """
    category = None

    # 🏎️ Redis cached categories
    categories = cache.get('global_store_categories')
    if not categories:
        categories = Category.objects.all()
        cache.set('global_store_categories', categories, 60 * 15)

    # Base Queryset: Unsold items ordered by latest additions
    products_list = Product.objects.filter(is_sold=False).select_related('category').order_by('-id')

    # Read GET query filter parameters
    type_filter = request.GET.get('type') or category_slug
    brand_filter = request.GET.get('brand')
    search_query = request.GET.get('search')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    # Check if user has applied any filtering parameters
    has_active_filters = bool(type_filter or brand_filter or search_query or min_price or max_price)

    # 1. Device Type / Category Filter
    if type_filter:
        products_list = products_list.filter(
            Q(category__slug__iexact=type_filter) | Q(category__name__icontains=type_filter)
        )

    # 2. Brand / Model Filter
    if brand_filter:
        products_list = products_list.filter(brand__iexact=brand_filter)

    # 3. Text Search Query Filter
    if search_query:
        products_list = products_list.filter(
            Q(name__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # 4. Price Range Filters
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

    # Gather available brands for filter selection dropdown
    available_brands = Product.objects.filter(is_sold=False).values_list('brand', flat=True).distinct()

    # Pagination engine (12 products per page = 3 rows of 4 products)
    paginator = Paginator(products_list.distinct(), 12)
    page_number = request.GET.get('page')

    try:
        products = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        products = paginator.page(1)

    # Grouped rows for default view without filters (4 items per category row)
    grouped_sections = {}
    if not has_active_filters:
        grouped_sections = {
            'phones': Product.objects.filter(is_sold=False, category__name__icontains='phone').order_by('-id')[:4],
            'laptops': Product.objects.filter(is_sold=False, category__name__icontains='laptop').order_by('-id')[:4],
            'tablets': Product.objects.filter(is_sold=False, category__name__icontains='tablet').order_by('-id')[:4],
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
    product = get_object_or_404(Product, slug=product_slug, is_sold=False)
    return render(request, 'shop/product/detail.html', {'product': product})


# ==========================================
# 🔐 AUTHENTICATION & REGISTRATION CUSTOMERS
# ==========================================

def register_customer(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone_number')
        passport = request.POST.get('passport_number')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return redirect('shop:register')
        if UserProfile.objects.filter(passport_number=passport).exists():
            messages.error(request, "This passport is already registered to another account.")
            return redirect('shop:register')

        new_user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        UserProfile.objects.create(
            user=new_user,
            phone_number=phone,
            passport_number=passport
        )

        login(request, new_user)
        messages.success(request, f"Welcome to TechVault, {first_name}!")
        return redirect('shop:home')

    return render(request, 'shop/auth/register.html')


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
    cart.add(product=product, quantity=1)
    messages.success(request, f"{product.name} added to cart!")
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
# 💎 STRATEGIC PROFILE SETTINGS INFRASTRUCTURE
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
# 🧾 TRANSACTIONAL CHECKOUT & HISTORY ORDERS
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

    flask_url = "http://127.0.0.1:8002/api/v1/generate-invoice"
    payload = {
        "order_id": str(order.id),
        "customer_name": f"{request.user.first_name} {request.user.last_name}" if request.user.first_name else request.user.username,
        "product_name": f"{product.brand} {product.name}",
        "price": str(product.price)
    }

    try:
        response = requests.post(flask_url, json=payload, timeout=5)
        if response.status_code == 201:
            messages.success(request, f"Success! Order #{order.id} processed. Your background PDF receipt is ready!")
            request.session['techvault_cart'] = {}
        else:
            messages.warning(request, "Order logged, but invoice background worker returned an error.")
    except requests.exceptions.ConnectionError:
        messages.warning(request, "Order logged securely, but background receipt microservice is currently offline.")

    return redirect('shop:product_list')


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/auth/order_history.html', {'orders': orders})


# ==========================================
# 📄 AUXILIARY STATIC PAGES
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

    all_products = Product.objects.filter(is_sold=False).order_by('-id')

    context = {
        'form': form,
        'product_instance': product_instance,
        'all_products': all_products,
    }
    return render(request, 'shop/product/create.html', context)