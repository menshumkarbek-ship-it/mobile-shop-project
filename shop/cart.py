from decimal import Decimal
from django.conf import settings
from .models import Product


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)

        # 🔒 Prevent adding the exact same product if it is already in the cart
        if product_id in self.cart and not override_quantity:
            return False  # Already in cart

        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price),
                'image': product.image.url if product.image else ''
            }

        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        self.save()
        return True

    def save(self):
        self.session.modified = True

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        product_ids = self.cart.keys()

        # 🧹 Automatic validation: filter out any products that were purchased and marked as is_sold=True by anyone
        valid_products = Product.objects.filter(id__in=product_ids, is_sold=False)
        valid_product_ids = {str(p.id) for p in valid_products}

        # Automatically purge sold items from current session carts
        keys_to_delete = [pid for pid in product_ids if pid not in valid_product_ids]
        for pid in keys_to_delete:
            del self.cart[pid]
            self.save()

        products = {str(p.id): p for p in valid_products}

        for product_id in self.cart.keys():
            if product_id in products:
                item = self.cart[product_id].copy()
                item['product'] = products[product_id]
                item['price'] = Decimal(item['price'])
                item['total_price'] = item['price'] * item['quantity']
                yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.save()