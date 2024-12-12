from django.db import models
from django.contrib.auth.models import User
from catalog.models import Book
from django.contrib.auth.models import AbstractUser, Group, Permission
from order.models import Payment, Order
from uuid import uuid4


# WishList Model
class WishList(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    books = models.ManyToManyField(Book)

    def __str__(self):
        return f"Wishlist for {self.user.username}"
    
    
class Contact(models.Model):
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contact from {self.firstname}"
    
    
class Receipt(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='receipts')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    issued_at = models.DateTimeField(auto_now_add=True)
    book_titles = models.TextField(help_text="Comma-separated list of book titles")
    is_downloaded = models.BooleanField(default=False)
    receipt_pdf = models.FileField(upload_to='receipts/', null=True, blank=True)  # Field to store the PDF

    def __str__(self):
        return f"Receipt for Order {self.order.id} by {self.user.username}"

    def get_book_titles(self):
        """Returns a list of book titles for the order."""
        return self.book_titles.split(', ')

    def total_price(self):
        """Fetches the total price from the order if needed."""
        return self.amount