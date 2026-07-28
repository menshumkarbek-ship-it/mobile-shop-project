from decimal import Decimal
from django.conf import settings
from .models import Product


class Cart:
    def __init__(self, request):
        """
        Initialize the shopping cart using Django sessions.
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # Create an empty cart in the session if none exists
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        """
        Add a device to the cart or update its quantity.
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price)
            }

        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        self.save()

    def save(self):
        # Mark the session as modified to make sure it gets saved to PostgreSQL
        self.session.modified = True

    def remove(self, product):
        """
        Remove a device completely from the cart.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        """
        Loop through the items in the cart and fetch the corresponding Product objects.
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)

        cart = self.cart.copy()
        for product in products:
            cart[str(product.id)]['product'] = product

        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """
        Count all items in the cart.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """
        Calculate total cart cost.
        """
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        """
        Wipe the cart out of the session.
        """
        del self.session[settings.CART_SESSION_ID]
        self.save()