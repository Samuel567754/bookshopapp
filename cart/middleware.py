from .models import Book, Cart, CartItem

class TransferCartMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and 'cart' in request.session:
            cart, created = Cart.objects.get_or_create(user=request.user)
            session_cart = request.session.pop('cart', {})
            
            for book_id, quantity in session_cart.items():
                book = Book.objects.get(id=book_id)
                cart_item, created = CartItem.objects.get_or_create(cart=cart, book=book)
                
                # Update or set quantity
                cart_item.quantity += quantity
                cart_item.save()
                
        response = self.get_response(request)
        return response
