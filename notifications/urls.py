from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notifications_view, name='notifications_view'),  # View all notifications
    path('mark_as_read/<int:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('clear_notifications/', views.clear_notifications, name='clear_notifications'),
    path('notifications/delete/<int:notification_id>/', views.delete_notification, name='delete_notification'),
    # Other paths...
    path('notifications/mark-shown/<int:notification_id>/', views.mark_notification_as_shown, name='mark_notification_as_shown'),
    path('notifications/view-all/', views.view_all_notifications, name='view_all_notifications'),
]