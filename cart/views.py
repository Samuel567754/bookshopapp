from django.shortcuts import render, get_object_or_404, redirect  # Render templates, get objects, redirect users
from django.http import JsonResponse, HttpResponseRedirect        # JSON responses, HTTP redirection
from django.urls import reverse                                  # URL reversing for named URLs
from django.db.models import Q                                   # Complex query filters (optional)
from django.views.decorators.csrf import csrf_exempt             # CSRF exemption for specific views if needed
from django.contrib.auth.decorators import login_required        # Enforce login requirement for views
from django.contrib import messages                              # Flash messages for user feedback
from catalog.models import Book                                  # Importing related model for cart item operations
from .models import Cart, CartItem                         # Cart and CartItem models for database interactions
from django.contrib.auth import login, logout, authenticate
from django.contrib.sessions.backends.db import SessionStore  # For advanced session handling
from django.contrib.sessions.models import Session
from user.models import WishList  
from django.conf import settings
from order.models import  Order 
from notifications.models import Notification





def add_to_cart(request, pk):
    # Retrieve the book instance
    book = get_object_or_404(Book, pk=pk)

    if request.user.is_authenticated:
        # Get or create the user's wishlist and cart
        wishlist, _ = WishList.objects.get_or_create(user=request.user)
        cart, _ = Cart.objects.get_or_create(user=request.user)

        # Check if the book is in the wishlist
        if wishlist.books.filter(pk=pk).exists():
            # Remove from wishlist and notify user
            wishlist.books.remove(book)
            messages.info(request, f'{book.title} was removed from your wishlist and added to your cart.')

            # Create a notification for removing from wishlist
            Notification.objects.create(
                user=request.user,
                title="Removed from Wishlist",
                message=f"{book.title} was removed from your wishlist and added to your cart."
            )

        # Add to cart or update quantity if it already exists
        cart_item, created = CartItem.objects.get_or_create(cart=cart, book=book)
        if created:
            messages.success(request, f'{book.title} has been added to your cart.')

            # Create a notification for adding to cart
            Notification.objects.create(
                user=request.user,
                title="Added to Cart",
                message=f"{book.title} has been added to your cart."
            )
        else:
            cart_item.quantity += 1
            cart_item.save()
            messages.info(request, f'{book.title} quantity was increased in your cart.')

            # Create a notification for updating cart item quantity
            Notification.objects.create(
                user=request.user,
                title="Cart Updated",
                message=f"The quantity of {book.title} was updated in your cart."
            )

    else:
        # Guest users: session-based cart
        session_cart = request.session.get('cart', {})
        str_pk = str(pk)  # Convert pk to string for session key

        # Update quantity or add new item in session cart
        if str_pk in session_cart:
            session_cart[str_pk] += 1
            messages.info(request, f'{book.title} quantity was increased in your cart.')
        else:
            session_cart[str_pk] = 1
            messages.success(request, f'{book.title} has been added to your cart.')

        # Save the session cart
        request.session['cart'] = session_cart
        request.session.modified = True

    # Redirect to cart page
    return redirect('cart_detail')

# def add_to_cart(request, pk):
#     # Retrieve the book instance
#     book = get_object_or_404(Book, pk=pk)

#     if request.user.is_authenticated:
#         # Get or create the user's wishlist and cart
#         wishlist, _ = WishList.objects.get_or_create(user=request.user)
#         cart, _ = Cart.objects.get_or_create(user=request.user)

#         # Check if the book is in the wishlist
#         if wishlist.books.filter(pk=pk).exists():
#             # Remove from wishlist and notify user
#             wishlist.books.remove(book)
#             messages.info(request, f'{book.title} was removed from your wishlist and added to your cart.')

#         # Add to cart or update quantity if it already exists
#         cart_item, created = CartItem.objects.get_or_create(cart=cart, book=book)
#         if created:
#             messages.success(request, f'{book.title} has been added to your cart.')
#         else:
#             cart_item.quantity += 1
#             # cart_item.save()
#             messages.info(request, f' {book.title} is already in your cart.')

#     else:
#         # Guest users: session-based cart
#         session_cart = request.session.get('cart', {})
#         str_pk = str(pk)  # Convert pk to string for session key
        
#         # Update quantity or add new item in session cart
#         if str_pk in session_cart:
#             session_cart[str_pk] = 1
#             messages.success(request, f' {book.title} is already in your cart.')
#         else:
#             session_cart[str_pk] = 1
#             messages.success(request, f'{book.title} has been added to your cart.')

#         # Save the session cart
#         request.session['cart'] = session_cart
#         request.session.modified = True

#     # Redirect to cart page
#     return redirect('cart_detail')



# View to display the cart items
def cart_detail(request):
    cart_items = []
    total_price = 0

    if request.user.is_authenticated:
        cart = get_object_or_404(Cart, user=request.user)
        for item in cart.cart_items.all():
            original_price = item.book.price
            discounted_price = item.book.discount_price if item.book.discount_price > 0 else original_price
            subtotal = discounted_price * item.quantity
            cart_items.append({
                'book': item.book,
                'quantity': item.quantity,
                'subtotal': subtotal,
                'original_price': original_price * item.quantity,
                'discounted_price': discounted_price * item.quantity,
            })
            total_price += subtotal
    else:
        session_cart = request.session.get('cart', {})
        for book_id, quantity in session_cart.items():
            book = Book.objects.get(id=book_id)
            original_price = book.price
            discounted_price = book.discount_price if book.discount_price > 0 else original_price
            subtotal = discounted_price * quantity
            cart_items.append({
                'book': book,
                'quantity': quantity,
                'subtotal': subtotal,
                'original_price': original_price * quantity,
                'discounted_price': discounted_price * quantity,
            })
            total_price += subtotal

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'cart/cart_detail.html', context)
# Update the cart item quantity for both authenticated users and guests

def update_cart_item(request, cart_item_id):
    if request.user.is_authenticated:
        cart_item = get_object_or_404(CartItem, id=cart_item_id)
    else:
        cart_item = None  # Handle guest logic below

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity'))
        
        if request.user.is_authenticated:
            # For logged-in users
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
                messages.success(request, 'Cart item quantity updated.')
            else:
                cart_item.delete()
                messages.success(request, 'Cart item removed.')
        else:
            # For guest users - session-based cart handling
            session_cart = request.session.get('cart', {})
            book_id = str(cart_item_id)
            
            if book_id in session_cart:
                if quantity > 0:
                    session_cart[book_id] = quantity
                    messages.success(request, 'Cart item quantity updated.')
                else:
                    del session_cart[book_id]
                    messages.success(request, 'Cart item removed.')
                
            request.session['cart'] = session_cart

    return redirect('cart_detail')



# Clear the entire cart
def clear_cart(request):
    if request.user.is_authenticated:
        cart = get_object_or_404(Cart, user=request.user)
        cart.cart_items.all().delete()
        messages.success(request, 'Cart cleared.')

        # Create a notification for clearing the cart
        Notification.objects.create(
            user=request.user,
            title="Cart Cleared",
            message="Your cart has been cleared."
        )
    else:
        # Guest cart clearing
        request.session['cart'] = {}
        messages.success(request, 'Cart cleared.')

        # Optional: If you want to handle guest notifications, you could add logic here
        # to inform guest users or simply skip this step for guests.

    return redirect('cart_detail')



# def clear_cart(request):
#     if request.user.is_authenticated:
#         cart = get_object_or_404(Cart, user=request.user)
#         cart.cart_items.all().delete()
#         messages.success(request, 'Cart cleared.')
#     else:
#         # Guest cart clearing
#         request.session['cart'] = {}
#         messages.success(request, 'Cart cleared.')

#     return redirect('cart_detail')


@login_required
def checkout_view(request):
    # Ensure the user is authenticated
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to access the checkout.")
        return redirect('login')

    # Retrieve the user's cart and calculate total price
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = []
    total_price = 0

    for item in cart.cart_items.all():
        original_price = item.book.price
        discounted_price = item.book.discount_price if item.book.discount_price > 0 else original_price
        subtotal = discounted_price * item.quantity
        cart_items.append({
            'book': item.book,
            'quantity': item.quantity,
            'subtotal': subtotal,
            'original_price': original_price * item.quantity,
            'discounted_price': discounted_price * item.quantity,
        })
        total_price += subtotal

    # Pass total_price to the template without creating an Order
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'user_info': request.user,
    }
    return render(request, 'cart/checkout.html', context)


# Remove a cart item for both authenticated users and guests
# def remove_cart_item(request, pk):
    
#     if request.user.is_authenticated:
#         # For authenticated users, filter by user and the book's primary key
#         cart_item = get_object_or_404(CartItem, book__pk=pk)
#         cart_item.delete()
#         messages.success(request, 'Cart item removed.')
#     else:
#         # Guest cart handling
#         session_cart = request.session.get('cart', {})
#         book_id = str(pk)
        
#         if book_id in session_cart:
#             del session_cart[book_id]
#             request.session['cart'] = session_cart
#             messages.success(request, 'Cart item removed.')

#     return redirect('cart_detail')

def remove_cart_item(request, pk):
    if request.user.is_authenticated:
        # For authenticated users, filter by user and the book's primary key
        cart_item = get_object_or_404(CartItem, cart__user=request.user, book__pk=pk)
        cart_item.delete()
        messages.success(request, 'Cart item removed.')

        # Create a notification for removing the item from the cart
        Notification.objects.create(
            user=request.user,
            title="Item Removed from Cart",
            message=f"{cart_item.book.title} was removed from your cart."
        )
    else:
        # Guest cart handling (no notifications added)
        session_cart = request.session.get('cart', {})
        book_id = str(pk)
        
        if book_id in session_cart:
            del session_cart[book_id]
            request.session['cart'] = session_cart
            messages.success(request, 'Cart item removed.')

    return redirect('cart_detail')
