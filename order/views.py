from django.shortcuts import render
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from .models import Order, OrderItem, Payment, Download
from catalog.models import Book
from django.contrib.auth.decorators import login_required
from django.urls import reverse
import json
from django.contrib import messages 
import requests
from django.conf import settings
from cart.models import Cart, CartItem  
from user.models import WishList, Receipt
from notifications.models import Notification

from user.views import generate_receipt_pdf, send_receipt_email  # Assuming these helper functions exist



@login_required
def buy_now(request, pk):
    # Get the selected book
    book = get_object_or_404(Book, pk=pk)
    
    # Check if the user has already purchased this book with a completed order status
    if OrderItem.objects.filter(order__user=request.user, book=book, order__status='completed').exists():
        messages.info(request, f"You have already purchased {book.title}. Redirecting to your downloads.")
        return redirect('order:download_page')  # Adjust to your actual downloads URL name

    # Get the user's wishlist
    wishlist, created = WishList.objects.get_or_create(user=request.user)

    # Check if the book is in the wishlist and remove it
    if wishlist.books.filter(id=book.id).exists():
        wishlist.books.remove(book)
        messages.info(request, f"{book.title} was removed from your wishlist.")

        # Create a notification for removing the item from the wishlist
        Notification.objects.create(
            user=request.user,
            title="Removed from Wishlist",
            message=f"{book.title} was removed from your wishlist as you proceeded to buy now."
        )

    # Get the user's cart or create one if it doesn't exist
    cart, created = Cart.objects.get_or_create(user=request.user)

    # Clear existing items in the cart to ensure it's a single-item transaction
    cart.cart_items.all().delete()  # Adjust to 'cartitem_set' if your related_name is different

    # Add the selected book to the cart with a quantity of 1
    cart_item, created = CartItem.objects.get_or_create(cart=cart, book=book, defaults={'quantity': 1})

    # Create a notification for adding the item to the cart for checkout
    Notification.objects.create(
        user=request.user,
        title="Added to Cart",
        message=f"{book.title} has been added to your cart for checkout."
    )

    # Redirect to the checkout page
    return redirect('checkout')





# @login_required
# def buy_now(request, pk):
#     # Get the selected book
#     book = get_object_or_404(Book, pk=pk)
    
#    # Check if the user has already purchased this book with a completed order status
#     if OrderItem.objects.filter(order__user=request.user, book=book, order__status='completed').exists():
#         messages.info(request, f"You have already purchased {book.title}. Redirecting to your downloads.")
#         return redirect('order:download_page')  # Adjust to your actual downloads URL name


#     # Get the user's wishlist
#     wishlist, created = WishList.objects.get_or_create(user=request.user)

#     # Check if the book is in the wishlist and remove it
#     if wishlist.books.filter(id=book.id).exists():
#         wishlist.books.remove(book)
#         messages.info(request, f"{book.title} was removed from your wishlist.")

#     # Get the user's cart or create one if it doesn't exist
#     cart, created = Cart.objects.get_or_create(user=request.user)

#     # Clear existing items in the cart to ensure it's a single-item transaction
#     cart.cart_items.all().delete()  # Adjust to 'cartitem_set' if your related_name is different

#     # Add the selected book to the cart with a quantity of 1
#     cart_item, created = CartItem.objects.get_or_create(cart=cart, book=book, defaults={'quantity': 1})

#     # Redirect to the checkout page
#     return redirect('checkout')

@login_required
def download_page(request):
    downloads = Download.objects.filter(user=request.user)
    download_count = Download.objects.filter(user=request.user).count()
    # Display all receipts in the user's dashboard
    receipts = Receipt.objects.filter(user=request.user).order_by('-issued_at')
    
    
    context = {
        'download_count': download_count,
        'downloads': downloads,
        'receipts': receipts,
        # Add any other context variables you need for your profile view
    }
    
    return render(request, 'order/downloads.html', context)


# View to display the order summary
@login_required
def order_summary(request):
    order = get_object_or_404(Order, user=request.user, status='pending')
    context = {'order': order}
    return render(request, 'orders/order_summary.html', context)


# View to initiate the payment using Paystack
# @login_required
# def initiate_payment(request):
#     # Fetch user's cart and calculate the total price
#     cart = get_object_or_404(Cart, user=request.user)
#     total_price = sum(
#         (item.book.discount_price if item.book.discount_price > 0 else item.book.price) * item.quantity
#         for item in cart.cart_items.all()
#     )

#     # Create the order and save each cart item as an OrderItem
#     order = Order.objects.create(
#         user=request.user,
#         status='pending',
#         amount=total_price,
#     )
    
#     # Create OrderItems for each cart item
#     for cart_item in cart.cart_items.all():
#         OrderItem.objects.create(
#             order=order,
#             book=cart_item.book,
#             price=(cart_item.book.discount_price if cart_item.book.discount_price > 0 else cart_item.book.price) * cart_item.quantity
#         )

#     # Initialize Paystack payment
#     headers = {
#         "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
#         "Content-Type": "application/json"
#     }
#     data = {
#         "email": request.user.email,
#         "amount": int(total_price * 100),  # Convert to kobo for Paystack
#         "currency": "GHS",
#         "callback_url": request.build_absolute_uri(reverse('order:verify_payment'))
#     }

#     response = requests.post('https://api.paystack.co/transaction/initialize', headers=headers, json=data)
#     res = response.json()

#     if res.get('status'):
#         # Save transaction ID in the order
#         order.transaction_id = res['data']['reference']
#         order.save()
#         return redirect(res['data']['authorization_url'])
#     else:
#         return JsonResponse({'message': 'Payment initiation failed'}, status=400)

# @login_required
# def verify_payment(request):
#     reference = request.GET.get('reference')
#     headers = {
#         "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
#     }

#     # Verify payment status
#     response = requests.get(f'https://api.paystack.co/transaction/verify/{reference}', headers=headers)
#     res = response.json()

#     if res.get('status') and res['data']['status'] == 'success':
#         try:
#             order = Order.objects.get(transaction_id=reference, user=request.user)

#             # Check if payment already exists
#             payment, created = Payment.objects.get_or_create(
#                 transaction_id=reference,
#                 defaults={
#                     'user': request.user,
#                     'order': order,
#                     'amount': order.amount,
#                     'status': 'completed',
#                     'payment_method': 'paystack'
#                 }
#             )

#             # If payment was created, update the order status to completed
#             if created:
#                 order.status = 'completed'
#                 order.save()

#                 # Grant download access for each order item
#                 for item in order.order_items.all():
#                     Download.objects.get_or_create(user=request.user, book=item.book)

#                 # Clear the user's cart after successful purchase
#                 cart = get_object_or_404(Cart, user=request.user)
#                 cart.cart_items.all().delete()
#             else:
#                 # Payment already exists; update order status if needed
#                 if order.status != 'completed':
#                     order.status = 'completed'
#                     order.save()

#             return redirect('order:order_success')
#         except Order.DoesNotExist:
#             return JsonResponse({'message': 'Order does not exist'}, status=400)
#     else:
#         return JsonResponse({'message': 'Payment verification failed'}, status=400)


@login_required
def initiate_payment(request):
    # Fetch user's cart and calculate the total price
    cart = get_object_or_404(Cart, user=request.user)
    total_price = sum(
        (item.book.discount_price if item.book.discount_price > 0 else item.book.price) * item.quantity
        for item in cart.cart_items.all()
    )

    # Create the order and save each cart item as an OrderItem
    order = Order.objects.create(
        user=request.user,
        status='pending',
        amount=total_price,
    )
    
    # Create OrderItems for each cart item
    for cart_item in cart.cart_items.all():
        OrderItem.objects.create(
            order=order,
            book=cart_item.book,
            price=(cart_item.book.discount_price if cart_item.book.discount_price > 0 else cart_item.book.price) * cart_item.quantity
        )

    # Initialize Paystack payment
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "email": request.user.email,
        "amount": int(total_price * 100),  # Convert to kobo for Paystack
        "currency": "GHS",
        "callback_url": request.build_absolute_uri(reverse('order:verify_payment'))
    }

    response = requests.post('https://api.paystack.co/transaction/initialize', headers=headers, json=data)
    res = response.json()

    if res.get('status'):
        # Save transaction ID in the order
        order.transaction_id = res['data']['reference']
        order.save()

        # Notification for payment initiation
        Notification.objects.create(
            user=request.user,
            title="Payment Initiated",
            message="Your payment has been initiated. You will be redirected to Paystack to complete the payment."
        )

        return redirect(res['data']['authorization_url'])
    else:
        # Notification for failed payment initiation
        Notification.objects.create(
            user=request.user,
            title="Payment Failed",
            message="There was an error initiating your payment. Please try again."
        )
        return JsonResponse({'message': 'Payment initiation failed'}, status=400)

# @login_required
# def verify_payment(request):
#     reference = request.GET.get('reference')
#     headers = {
#         "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
#     }

#     # Verify payment status
#     response = requests.get(f'https://api.paystack.co/transaction/verify/{reference}', headers=headers)
#     res = response.json()

#     if res.get('status') and res['data']['status'] == 'success':
#         try:
#             order = Order.objects.get(transaction_id=reference, user=request.user)

#             # Check if payment already exists
#             payment, created = Payment.objects.get_or_create(
#                 transaction_id=reference,
#                 defaults={
#                     'user': request.user,
#                     'order': order,
#                     'amount': order.amount,
#                     'status': 'completed',
#                     'payment_method': 'paystack'
#                 }
#             )

#             # If payment was created, update the order status to completed
#             if created:
#                 order.status = 'completed'
#                 order.save()

#                 # Grant download access for each order item
#                 for item in order.order_items.all():
#                     Download.objects.get_or_create(user=request.user, book=item.book)

#                 # Clear the user's cart after successful purchase
#                 cart = get_object_or_404(Cart, user=request.user)
#                 cart.cart_items.all().delete()

#                 # Notification for successful payment and download access
#                 Notification.objects.create(
#                     user=request.user,
#                     title="Payment Successful",
#                     message="Your payment was successful. You can now download your purchased books."
#                 )
#             else:
#                 # Payment already exists; update order status if needed
#                 if order.status != 'completed':
#                     order.status = 'completed'
#                     order.save()

#             return redirect('order:order_success')
#         except Order.DoesNotExist:
#             return JsonResponse({'message': 'Order does not exist'}, status=400)
#     else:
#         # Notification for failed payment verification
#         Notification.objects.create(
#             user=request.user,
#             title="Payment Verification Failed",
#             message="There was an error verifying your payment. Please contact support if the issue persists."
#         )
#         return JsonResponse({'message': 'Payment verification failed'}, status=400)


@login_required
def verify_payment(request):
    reference = request.GET.get('reference')
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }

    # Verify payment status
    response = requests.get(f'https://api.paystack.co/transaction/verify/{reference}', headers=headers)
    res = response.json()

    if res.get('status') and res['data']['status'] == 'success':
        try:
            order = Order.objects.get(transaction_id=reference, user=request.user)

            # Check if payment already exists
            payment, created = Payment.objects.get_or_create(
                transaction_id=reference,
                defaults={
                    'user': request.user,
                    'order': order,
                    'amount': order.amount,
                    'status': 'completed',
                    'payment_method': 'paystack'
                }
            )

            # If payment was created, update the order status to completed
            if created:
                order.status = 'completed'
                order.save()

                # Grant download access for each order item
                for item in order.order_items.all():
                    Download.objects.get_or_create(user=request.user, book=item.book)

                # Clear the user's cart after successful purchase
                cart = get_object_or_404(Cart, user=request.user)
                cart.cart_items.all().delete()

                # Notification for successful payment and download access
                Notification.objects.create(
                    user=request.user,
                    title="Payment Successful",
                    message="Your payment was successful. You can now download your purchased books."
                )

                # Generate the receipt
                receipt = Receipt.objects.create(
                    order=order,
                    user=request.user,
                    transaction_id=reference,
                    amount=order.amount,
                    payment_method="paystack",
                    book_titles=", ".join([item.book.title for item in order.order_items.all()]),
                    is_downloaded=False
                )

                # Send the receipt via email
                send_receipt_email(request.user, receipt)

            else:
                # Payment already exists; update order status if needed
                if order.status != 'completed':
                    order.status = 'completed'
                    order.save()

            return redirect('order:order_success')
        except Order.DoesNotExist:
            return JsonResponse({'message': 'Order does not exist'}, status=400)
    else:
        # Notification for failed payment verification
        Notification.objects.create(
            user=request.user,
            title="Payment Verification Failed",
            message="There was an error verifying your payment. Please contact support if the issue persists."
        )
        return JsonResponse({'message': 'Payment verification failed'}, status=400)


@login_required
def order_success(request):
    return render(request, 'order/order_success.html')


@login_required
def download_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    # Check if user is allowed to download
    if Download.objects.filter(user=request.user, book=book).exists():
        if book.file:
            response = HttpResponse(book.file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{book.file.name}"'
            return response
        else:
            return HttpResponse("No file available for this book.")
    else:
        messages.error(request, "You are not authorized to download this book.")
        return redirect('order_summary')



