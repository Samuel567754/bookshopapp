# context_processors.py
from .models import Cart
from django.contrib.sessions.models import Session
from django.contrib import sessions
def cart_count(request):
    cart_count = 0
    session_cart = request.session.get('cart', {})
   
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart_count = cart.cart_items.count()
    else:
        # cart_count = sum(session_cart.values())
        cart_count = len(session_cart)


    return {'cart_count': cart_count}