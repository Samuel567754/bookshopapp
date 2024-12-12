from django.contrib import admin
from .models import Cart, CartItem

# Customizing the CartItemAdmin
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'book', 'quantity')  # Display the cart, book, and quantity in the list view
    search_fields = ('cart__user__username', 'book__title')  # Search by cart user and book title
    list_filter = ('quantity',)  # Filter by quantity of items

# Inline for CartItems within CartAdmin
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1  # Number of empty forms to display for adding new CartItems

# Customizing the CartAdmin
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'total_price_display')  # Display user, created_at, and total price
    search_fields = ('user__username',)  # Search by username
    readonly_fields = ('created_at', 'total_price_display')  # Make created_at and total price read-only
    ordering = ('-created_at',)  # Order by most recent carts
    inlines = [CartItemInline]  # Inline CartItem for easier management

    # Method to display total price in the admin list view
    def total_price_display(self, obj):
        return obj.total_price()

    total_price_display.short_description = 'Total Price'

# Registering the models and their admin customizations
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)



