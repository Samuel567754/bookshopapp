from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Notification
from django.template.loader import render_to_string
from django import template
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt




@login_required
def view_all_notifications(request):
    # Retrieve all notifications for the authenticated user
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notifications/view_all.html', {'notifications': notifications})



def mark_notification_as_shown(request, notification_id):
    if request.user.is_authenticated:
        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.shown = True
            notification.save()
            return JsonResponse({'success': True})
        except Notification.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Notification not found'})
    else:
        return JsonResponse({'success': False, 'error': 'User not authenticated'})
    
    
    

# @csrf_exempt
# def mark_notification_shown(request, notification_id):
#     if request.method == 'POST' and request.user.is_authenticated:
#         try:
#             notification = Notification.objects.get(id=notification_id, user=request.user)
#             notification.shown = True
#             notification.save()
#             return JsonResponse({'success': True})
#         except Notification.DoesNotExist:
#             return JsonResponse({'success': False, 'error': 'Notification not found'})
#     return JsonResponse({'success': False, 'error': 'Invalid request'})


@require_POST  # Only accept POST requests
def delete_notification(request, notification_id):
    if request.user.is_authenticated:
        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.delete()
            return JsonResponse({'success': True})
        except Notification.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Notification not found'})
    else:
        return JsonResponse({'success': False, 'error': 'User not authenticated'})
    
    
    
@login_required
def notifications_view(request):
    # This view will render a page with all notifications
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    notification_count = notifications.filter(is_read=False).count()

    context = {
        'notifications': notifications,
        'notification_count': notification_count
    }
    return render(request, 'notifications/notifications.html', context)



# def mark_notification_as_read(request, notification_id):
#     if request.user.is_authenticated:
#         notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        
#         # Mark the notification as read
#         notification.is_read = True
#         notification.save()

#         # Return success response
#         return JsonResponse({'success': True})

#     # If user is not authenticated or error, return failure response
#     return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)




def mark_notification_as_read(request, notification_id):
    try:
        # Retrieve and update the notification
        notification = Notification.objects.get(id=notification_id)
        notification.is_read = True
        notification.save()

        # Count unread notifications
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        
        return JsonResponse({'success': True, 'notification_count': unread_count})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'}, status=404)
    except Exception as e:
        print(f"Error: {e}")  # Log any other errors
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def clear_notifications(request):
    if request.method == "POST" and request.user.is_authenticated:
        # Mark all notifications as read
        notifications = Notification.objects.filter(user=request.user, is_read=False)
        notifications.update(is_read=True)

        # Optionally delete notifications
        # notifications.delete()

        # Fetch updated notifications and count
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        notification_count = notifications.filter(is_read=False).count()

        # Return updated notifications and count
        notification_data = [{
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'created_at': notification.created_at,
            'is_read': notification.is_read
        } for notification in notifications]

        return JsonResponse({'success': True, 'notifications': notification_data, 'notification_count': notification_count})

    return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)