from django.contrib import admin
from .models import Order, OrderItem, Payment, Download

# Customizing the OrderItemAdmin
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'book', 'price')  # Display order, book, and price in the list view
    search_fields = ('order__id', 'book__title')  # Search by order ID and book title
    list_filter = ('price',)  # Filter by price

# Inline model for OrderItems in OrderAdmin
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1  # Number of empty forms to display

# Customizing the OrderAdmin
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'amount', 'created_at', 'transaction_id', 'total_price_display')  
    search_fields = ('user__username', 'transaction_id')  # Search by username and transaction ID
    list_filter = ('status', 'created_at')  # Filter by status and creation date
    readonly_fields = ('created_at', 'total_price_display')  # Make the creation date and total price read-only
    ordering = ('-created_at',)  # Order by the most recent orders
    inlines = [OrderItemInline]  # Add inline OrderItems to the OrderAdmin
    
    # Method to display total price in the list view
    def total_price_display(self, obj):
        return obj.total_price()

    total_price_display.short_description = 'Total Price'

# Customizing the PaymentAdmin
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'order', 'amount', 'status', 'payment_method', 'created_at')  
    search_fields = ('transaction_id', 'user__username', 'order__id')  # Search by transaction ID, username, and order ID
    list_filter = ('status', 'payment_method')  # Filter by status and payment method
    ordering = ('-created_at',)  # Order by most recent payments

# Customizing the DownloadAdmin
class DownloadAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'downloaded_at')  # Display user, book, and download time in the list view
    search_fields = ('user__username', 'book__title')  # Search by username and book title
    list_filter = ('downloaded_at',)  # Filter by download date

# Registering the models and their admin customizations
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Download, DownloadAdmin)
