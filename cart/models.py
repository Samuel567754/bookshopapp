from django.db import models
from django.contrib.auth.models import User
from catalog.models import Book

# CartItem Model
class CartItem(models.Model):
    cart = models.ForeignKey('Cart', on_delete=models.CASCADE, related_name='cart_items')  # Changed related_name for clarity
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.book.title} in cart"

# Cart Model   
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        """Calculates the total price of items in the cart."""
        return sum(item.book.final_price() * item.quantity for item in self.cart_items.all())

    def __str__(self):
        return f"Cart for {self.user.username}"
