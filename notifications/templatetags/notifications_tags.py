from django import template
from notifications.models import Notification  # Adjust the import according to your app's name

register = template.Library()

@register.inclusion_tag('partials/_nav.html', takes_context=True)
def load_notifications(context):
    """
    Custom template tag to load notifications for the logged-in user.
    """
    user = context['request'].user
    notifications = Notification.objects.filter(user=user).order_by('-created_at')
    notification_count = notifications.filter(is_read=False).count()

    return {
        'notifications': notifications,
        'notification_count': notification_count,
    }
