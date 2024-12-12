# context_processors.py
from .models import Notification

def user_notifications(request):
    # Ensure that the user is authenticated
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        unread_notifications = notifications.filter(is_read=False, shown=False)
        notification_count = unread_notifications.count()
    else:
        notifications = []
        notification_count = 0

    return {
        'notifications': notifications,  # All notifications (unread and read)
        'notification_count': notification_count  # Count of unread notifications
    }



# context_processors.py
# from .models import Notification

# def user_notifications(request):
#     # Ensure that the user is authenticated
#     if request.user.is_authenticated:
#         # Only fetch unread and unshown notifications
#         notifications = Notification.objects.filter(
#             user=request.user,
#             is_read=False,
#             shown=False
#         ).order_by('-created_at')
#         notification_count = notifications.count()
#     else:
#         notifications = []
#         notification_count = 0

#     return {
#         'notifications': notifications,  # Only unread and unshown notifications
#         'notification_count': notification_count  # Count of unread notifications
#     }









# from .models import Notification

# def notification_count(request):
#     # Check if the user is authenticated
#     if request.user.is_authenticated:
#         # Get the count of unread notifications for the user
#         unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
#     else:
#         unread_count = 0  # If not logged in, set count to 0

#     # Return the count as a dictionary so it's accessible in templates
#     return {
#         'notification_count': unread_count
#     }