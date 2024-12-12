# urls.py
from django.urls import path
from . import views

app_name = 'order'

urlpatterns = [
    path('order-summary/', views.order_summary, name='order_summary'),
    path('initiate_payment/', views.initiate_payment, name='initiate_payment'),
    path('order/verify-payment/', views.verify_payment, name='verify_payment'),
    path('success/', views.order_success, name='order_success'),  # Ensure this line exists
    path('download_book/<int:book_id>/', views.download_book, name='download_book'),
    path('downloads/', views.download_page, name='download_page'),  # URL for downloads
    path('buy-now/<int:pk>/', views.buy_now, name='buy_now'),
]
