from django.urls import path
from . import views

urlpatterns = [
    path('add/<int:pk>/', views.add_to_cart, name='add_to_cart'),  # Add book to cart
    path('cart/details', views.cart_detail, name='cart_detail'),  # View cart details
    path('update/<int:cart_item_id>/', views.update_cart_item, name='update_cart_item'),  # Update cart item quantity
    path('remove/<int:pk>/', views.remove_cart_item, name='remove_cart_item'), # Remove an item from cart
    path('clear/', views.clear_cart, name='clear_cart'),  # Clear the cart
    path('checkout/', views.checkout_view, name='checkout'),
]
