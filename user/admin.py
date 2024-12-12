from django.contrib import admin
from .models import WishList, Contact, Receipt

class CantactAdmin(admin.ModelAdmin):
    list_display = ('firstname', 'lastname', 'phone', 'email', 'message')  # Show the user and the list of books in the wishlist
    search_fields = ('firstname', 'lastname')  # Search by user and book title
    list_filter = ('firstname','lastname')  # Filter by books
   
# Customizing the WishListAdmin
class WishListAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_books')  # Show the user and the list of books in the wishlist
    search_fields = ('user__username', 'books__title')  # Search by user and book title
    list_filter = ('books',)  # Filter by books
    filter_horizontal = ('books',)  # Add a filter widget for the ManyToMany relationship

    # Method to display books in the wishlist as comma-separated values
    def display_books(self, obj):
        return ", ".join([book.title for book in obj.books.all()])

    display_books.short_description = 'Books in Wishlist'
    
    

class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_id', 'amount', 'payment_method','receipt_pdf', 'issued_at', 'display_books', 'is_downloaded')
    search_fields = ('user__username', 'transaction_id')
    list_filter = ('payment_method', 'issued_at')
    
    def display_books(self, obj):
        """Display book titles as a comma-separated list."""
        return obj.book_titles
    display_books.short_description = 'Books in Receipt'


# Register the WishList model with its custom admin
admin.site.register(WishList, WishListAdmin)
admin.site.register(Contact, CantactAdmin)
admin.site.register(Receipt, ReceiptAdmin)
