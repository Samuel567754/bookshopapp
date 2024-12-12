from django.contrib import admin
from .models import Notification

# Define a custom admin for the Notification model
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title','message', 'is_read','shown', 'created_at')
    list_filter = ('is_read','shown', 'created_at')
    search_fields = ('title', 'user__username')
    actions = ['mark_as_read','shown', 'mark_as_unread']

    # Custom actions to mark notifications as read or unread
    @admin.action(description='Mark selected notifications as read')
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description='Mark selected notifications as unread')
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
