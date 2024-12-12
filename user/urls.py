from django.contrib import admin
from django.urls import path
from user import views as user_views
from django.contrib.auth import views as auth_views
from user.views import CustomPasswordResetView

urlpatterns = [
    # User Registration and Authentication
    path('register/', user_views.register, name='register'),
    path('login/', user_views.user_login, name='login'),
    path('logout/', user_views.user_logout, name='logout'),
    
    # Profile and User Dashboard
    path('profile/', user_views.profile, name='profile'),
    path('profile/overview/', user_views.profile_overview, name='profile_overview'),
    path('profile/edit/', user_views.edit_profile, name='edit_profile'),
    
    # Purchases and Downloads
    path('user/purchases/', user_views.user_purchases_view, name='user_purchases'),
    path('profile/downloads/', user_views.user_downloads, name='user_downloads'),
    path('download-receipt/<int:receipt_id>/', user_views.download_receipt, name='download_receipt'),
    path('user/receipts/', user_views.user_receipts, name='user_receipts'),
    
    # Wishlist
    path('wishlist/', user_views.wishlist_view, name='wishlist'),
    path('wishlist/add/<int:pk>/', user_views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:pk>/', user_views.remove_from_wishlist, name='remove_from_wishlist'),
    
    # Shop and Services
    path('shop/', user_views.shop, name='shop'),
    path('services/', user_views.services, name='services'),
    path('recommend-books/', user_views.recommend_books, name='recommend_books'),
    path('customer-support/', user_views.customer_support_chat, name='customer_support_chat'),
    
    # About and Contact
    path('aboutus/', user_views.about_us, name='about_us'),
    path('contact/', user_views.contact_view, name='contact'),
    path('contactus/', user_views.contact_us, name='contact_us'),
    path('contactsupport/', user_views.contact_support, name='contact_support'),
    
    # Orders and Notifications
    path('my-orders/', user_views.user_orders, name='user_orders'),
    path('user/notifications/', user_views.user_notifications, name='user_notifications'),
    
    # Account Activation
    path('activate/<uidb64>/<token>/', user_views.activate, name='activate'),
    path('account-activation-sent/', user_views.account_activation_sent, name='account_activation_sent'),
    
    # Password Reset
    path(
        'password-reset/',
        CustomPasswordResetView.as_view(
            template_name='user/registration/password_reset.html',  # Form page template
            email_template_name='user/emails/password_reset_email.html',  # Custom email template
            subject_template_name='user/emails/password_reset_subject.txt'  # Optional custom subject
        ),
        name='password_reset'
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(template_name='user/registration/password_reset_done.html'),
        name='password_reset_done'
    ),
    path(
        'password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(template_name='user/registration/password_reset_confirm.html'),
        name='password_reset_confirm'
    ),
    path(
        'password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(template_name='user/registration/password_reset_complete.html'),
        name='password_reset_complete'
    ),
]

    
#     # Using Django's built-in password change/reset views
#     path('password-reset/',
#          auth_views.PasswordResetView.as_view(template_name='user/password_reset.html'),
#          name='password_reset'),
#     path('password-reset/done/',
#          auth_views.PasswordResetDoneView.as_view(template_name='user/password_reset_done.html'),
#          name='password_reset_done'),
#     path('password-reset-confirm/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(template_name='user/password_reset_confirm.html'),
#          name='password_reset_confirm'),
#     path('password-reset-complete/',
#          auth_views.PasswordResetCompleteView.as_view(template_name='user/password_reset_complete.html'),
#          name='password_reset_complete'),










