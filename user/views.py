from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordResetView
from django.core.mail import send_mail, EmailMessage
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib import messages
from django.db.models import Count, Sum
from .forms import UserRegisterForm, UserEditForm, ContactForm
from .models import Book, WishList, Receipt
from .utils import get_user_purchased_books, get_user_books_count
from cart.models import Cart, CartItem
from order.models import Order, OrderItem, Download
from collections import Counter
from .tokens import account_activation_token
from notifications.models import Notification
from catalog.models import Category
from django.db.models import Q

# Additional imports (optional, based on your specific needs)
from django.urls import reverse  # For generating URLs
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode  # For encoding user IDs in verification emails
from django.utils.encoding import force_bytes, force_str  # For encoding/decoding bytes for tokens
from django.contrib.sites.shortcuts import get_current_site  # For multi-site projects, useful for email links


from django.core.files.storage import default_storage
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
import qrcode
import os
from django.http import HttpResponse

from django.conf import settings
from django.core.files.base import ContentFile
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import inch

from .utils import get_chatgpt_response  # Assuming the utility function is in utils.py



def recommend_books(request):
    query = request.GET.get('query', '')
    if query:
        prompt = f"Recommend books based on the theme: {query}."
        chatgpt_response = get_chatgpt_response(prompt)
    else:
        chatgpt_response = "Please provide a theme for recommendations."
    
    return render(request, 'user/recommend_books.html', {'response': chatgpt_response})


def customer_support_chat(request):
    user_query = request.POST.get('query', '')
    chat_response = get_chatgpt_response(user_query) if user_query else ''
    return render(request, 'user/customer_support_chat.html', {'response': chat_response})



def generate_receipt_pdf(receipt):
    # Create a QR code with the transaction details
    qr_data = f"Transaction ID: {receipt.transaction_id}, Amount: {receipt.amount}, Books: {receipt.get_book_titles()}"
    qr = qrcode.make(qr_data)

    # Save QR code to the file system using Django's storage system
    qr_image_io = BytesIO()
    qr.save(qr_image_io)
    qr_image_io.seek(0)
    qr_image_path = f"qr_codes/{receipt.transaction_id}.png"
    qr_image = ContentFile(qr_image_io.read(), name=qr_image_path)
    qr_image_path = default_storage.save(qr_image_path, qr_image)

    # Get the absolute file path for the QR code image
    qr_image_abs_path = default_storage.path(qr_image_path)

    # Start generating the PDF
    pdf_file = BytesIO()
    c = canvas.Canvas(pdf_file, pagesize=letter)
    
    # Header Section
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.navy)
    c.drawString(1 * inch, 10.5 * inch, "Your Company Name")
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(1 * inch, 10.2 * inch, "Order Receipt")
    
    # Adding a divider line
    c.setStrokeColor(colors.grey)
    c.setLineWidth(1)
    c.line(1 * inch, 10 * inch, 7.5 * inch, 10 * inch)

    # Table of Receipt Details
    data = [
        ["Order ID:", f"{receipt.order.id}"],
        ["User:", f"{receipt.user.username}"],
        ["Transaction ID:", f"{receipt.transaction_id}"],
        ["Amount Paid:", f"${receipt.amount}"],
        ["Payment Method:", f"{receipt.payment_method}"],
        ["Issued At:", f"{receipt.issued_at.strftime('%Y-%m-%d %H:%M:%S')}"]
    ]
    table = Table(data, colWidths=[2 * inch, 4 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    # Move the y-position for the table
    table.wrapOn(c, 400, 300)
    table.drawOn(c, 1 * inch, 8.5 * inch)

    # Books Section
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.navy)
    c.drawString(1 * inch, 8 * inch, "Books Purchased:")
    
    y_position = 7.7 * inch
    for title in receipt.get_book_titles():
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)
        c.drawString(1.2 * inch, y_position, f"- {title}")
        y_position -= 0.2 * inch

    # QR Code Section
    c.drawImage(qr_image_abs_path, 5.5 * inch, 6.5 * inch, width=1.5 * inch, height=1.5 * inch)
    c.setFont("Helvetica", 8)
    c.drawString(5.5 * inch, 6.3 * inch, "Scan to verify transaction")

    # Footer Section
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.grey)
    c.drawString(1 * inch, 0.5 * inch, "Thank you for your purchase!")
    c.drawRightString(7.5 * inch, 0.5 * inch, f"Page {c.getPageNumber()}")

    # Finalize and save the PDF
    c.save()
    pdf_file.seek(0)

    receipt_file_name = f"receipt_{receipt.transaction_id}.pdf"
    pdf_content = ContentFile(pdf_file.read())
    receipt.receipt_pdf.save(receipt_file_name, pdf_content, save=True)

    return pdf_content.read()



def send_receipt_email(user, receipt):
    # Generate the HTML email content
    email_subject = 'Your Purchase Receipt'
    email_body = render_to_string(
        'user/emails/receipt_email.html',  # Path to your HTML template
        {
            'user': user,
            'receipt': receipt,
            'book_titles': receipt.get_book_titles(),
        }
    )

    # Create the email message with HTML content
    email = EmailMessage(
        email_subject,
        email_body,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )
    email.content_subtype = "html"  # Ensure the content is sent as HTML

    # Attach the PDF receipt
    pdf_content = generate_receipt_pdf(receipt)
    email.attach('receipt.pdf', pdf_content, 'application/pdf')

    # Send the email
    email.send()
    
    
    
def user_receipts(request):
    # Display all receipts in the user's dashboard
    receipts = Receipt.objects.filter(user=request.user).order_by('-issued_at')
    return render(request, 'user/reciepts/user_receipts.html', {'receipts': receipts})

def download_receipt(request, receipt_id):
    # Provide a downloadable version of the receipt PDF
    receipt = get_object_or_404(Receipt, id=receipt_id, user=request.user)
    response = HttpResponse(receipt.receipt_pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{receipt.transaction_id}.pdf"'
    return response










class CustomPasswordResetView(PasswordResetView):
    def send_mail(self, subject, message, from_email, to_email, **kwargs):
        email = EmailMessage(subject, message, from_email, to_email, **kwargs)
        email.content_subtype = 'html'  # Set content subtype to HTML
        email.send()



@login_required
def user_downloads(request):
    downloads = Download.objects.filter(user=request.user)
    download_count = Download.objects.filter(user=request.user).count()
    
    context = {
        'download_count': download_count,
        'downloads': downloads,
        # Add any other context variables you need for your profile view
    }
    
    return render(request, 'user/downloads.html', context)


@login_required
def user_purchases_view(request):
    user = request.user
    purchased_books = get_user_purchased_books(user)
    book_orders = []
    for book in purchased_books:
        order_items = OrderItem.objects.filter(book=book)
        for order_item in order_items:
            book_orders.append(order_item.order)

    context = {
        'purchased_books': purchased_books,
        'book_orders': book_orders,
        'book_counts': get_user_books_count(user),
    }
    return render(request, 'user/user_purchases.html', context)





@login_required
def wishlist_view(request):
    wishlist, created = WishList.objects.get_or_create(user=request.user)
    books = wishlist.books.all()  # Retrieve all books in the wishlist
    context = {
        'wishlist': wishlist,
        'books': books,
    }
    return render(request, 'user/wishlist.html', context)


# @login_required
# def add_to_wishlist(request, pk):
#     book = get_object_or_404(Book, pk=pk)

#     # Check if the book is already in the user's cart
#     cart, created = Cart.objects.get_or_create(user=request.user)
#     if cart.cart_items.filter(pk=pk).exists():
#         messages.warning(request, f'{book.title} is already in your cart. Please remove it from your cart before adding to the wishlist.')
#         return redirect('cart_detail')  # Redirect to cart or wishlist, based on your design

#     wishlist, created = WishList.objects.get_or_create(user=request.user)
    
#     if not wishlist.books.filter(pk=pk).exists():
#         wishlist.books.add(book)
#         messages.success(request, f'{book.title} added to your wishlist.')
#     else:
#         messages.info(request, f'{book.title} is already in your wishlist.')

#     return redirect('wishlist')


@login_required
def add_to_wishlist(request, pk):
    book = get_object_or_404(Book, pk=pk)

    # Check if the book is already in the user's cart
    cart, created = Cart.objects.get_or_create(user=request.user)
    if cart.cart_items.filter(pk=pk).exists():
        messages.warning(request, f'{book.title} is already in your cart. Please remove it from your cart before adding to the wishlist.')

        # Notification for book already in cart
        Notification.objects.create(
            user=request.user,
            title="Book Already in Cart",
            message=f'{book.title} is already in your cart. Please remove it from your cart before adding to the wishlist.'
        )

        return redirect('cart_detail')  # Redirect to cart or wishlist, based on your design

    wishlist, created = WishList.objects.get_or_create(user=request.user)
    
    if not wishlist.books.filter(pk=pk).exists():
        wishlist.books.add(book)
        messages.success(request, f'{book.title} added to your wishlist.')

        # Notification for successful wishlist addition
        Notification.objects.create(
            user=request.user,
            title="Added to Wishlist",
            message=f'{book.title} has been added to your wishlist.'
        )
    else:
        messages.info(request, f'{book.title} is already in your wishlist.')

        # Notification for book already in wishlist
        Notification.objects.create(
            user=request.user,
            title="Already in Wishlist",
            message=f'{book.title} is already in your wishlist.'
        )

    return redirect('wishlist')



# @login_required
# def remove_from_wishlist(request, pk):
#     book = get_object_or_404(Book, pk=pk)
#     wishlist, created = WishList.objects.get_or_create(user=request.user)
    
#     if wishlist.books.filter(pk=pk).exists():
#         wishlist.books.remove(book)
#         messages.success(request, f"'{book.title}' has been removed from your wishlist.")
#     else:
#         messages.info(request, f"'{book.title}' was not in your wishlist.")
    
#     return redirect('wishlist')

@login_required
def remove_from_wishlist(request, pk):
    book = get_object_or_404(Book, pk=pk)
    wishlist, created = WishList.objects.get_or_create(user=request.user)
    
    if wishlist.books.filter(pk=pk).exists():
        wishlist.books.remove(book)
        messages.success(request, f"'{book.title}' has been removed from your wishlist.")
        
        # Notification for successful removal
        Notification.objects.create(
            user=request.user,
            title="Removed from Wishlist",
            message=f"'{book.title}' has been removed from your wishlist."
        )
    else:
        messages.info(request, f"'{book.title}' was not in your wishlist.")
        
        # Notification for not in wishlist
        Notification.objects.create(
            user=request.user,
            title="Not in Wishlist",
            message=f"'{book.title}' was not in your wishlist."
        )
    
    return redirect('wishlist')




# @login_required
# def edit_profile(request):
#     if request.method == 'POST':
#         form = UserEditForm(request.POST, instance=request.user)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Your profile has been updated successfully.')
#             return redirect('profile')  # Redirect after saving
#         else:
#             print(form.errors) 
#             messages.error(request, f'profile update failed!')
#     else:
#         form = UserEditForm(instance=request.user)

#     return render(request, 'user/edit_profile.html', {'form': form})


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            
            # Notification for successful profile update
            Notification.objects.create(
                user=request.user,
                title="Profile Updated",
                message="Your profile has been updated successfully."
            )
            
            return redirect('profile')  # Redirect after saving
        else:
            print(form.errors) 
            messages.error(request, 'Profile update failed!')
            
            # Notification for failed profile update
            Notification.objects.create(
                user=request.user,
                title="Profile Update Failed",
                message="There was an issue updating your profile. Please try again."
            )
    else:
        form = UserEditForm(instance=request.user)

    return render(request, 'user/edit_profile.html', {'form': form})





@login_required
def profile_overview(request):
    user = request.user
    context = {
        'user': user,
    }
    return render(request, 'user/profile_overview.html', context)
# def register(request):
#     if request.method == 'POST':
#         form = UserRegisterForm(request.POST)
#         if form.is_valid():
#             form.save()
#             username = form.cleaned_data.get('username')
#             messages.success(request, f'Account created for {username}!')
#             return redirect('login')  # Redirect to login after registration
#         # else:
#         #     messages.error(request, f'Account creation failed!')
#         #     return redirect('register')  # Redirect to login after registration
#     else:
#         form = UserRegisterForm()
#     return render(request, 'user/register.html', {'form': form})


@login_required
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)  # Don’t save to the database yet
            user.is_active = False  # Deactivate account until it is confirmed
            user.save()

            # Generate email verification token
            current_site = get_current_site(request)
            mail_subject = 'Activate your account.'
            message = render_to_string('user/emails/activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.send()

            # Notification for successful registration
            Notification.objects.create(
                user=user,
                title="Registration Successful",
                message=f"Account created for {user.username}! Please confirm your email address to complete registration."
            )

            messages.success(request, f'Account created for {user.username}! Please confirm your email address to complete registration.')
            return redirect('account_activation_sent')
    else:
        form = UserRegisterForm()
    return render(request, 'user/register.html', {'form': form})




# def register(request):
#     if request.method == 'POST':
#         form = UserRegisterForm(request.POST)
#         if form.is_valid():
#             user = form.save(commit=False)  # Don’t save to the database yet
#             user.is_active = False  # Deactivate account until it is confirmed
#             user.save()

#             # Generate email verification token
#             current_site = get_current_site(request)
#             mail_subject = 'Activate your account.'
#             message = render_to_string('user/emails/activation_email.html', {
#                 'user': user,
#                 'domain': current_site.domain,
#                 'uid': urlsafe_base64_encode(force_bytes(user.pk)),
#                 'token': account_activation_token.make_token(user),
#             })
#             to_email = form.cleaned_data.get('email')
#             email = EmailMessage(mail_subject, message, to=[to_email])
#             email.send()

#             messages.success(request, f'Account created for {user.username}! Please confirm your email address to complete registration.')
#             return redirect('account_activation_sent')
#     else:
#         form = UserRegisterForm()
#     return render(request, 'user/register.html', {'form': form})


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)

        # Create a notification for successful activation
        Notification.objects.create(
            user=user,
            title="Account Activated",
            message="Your account has been activated successfully! You can now log in."
        )

        messages.success(request, 'Your account has been activated successfully!')
        return redirect('login')
    else:
        # Create a notification for failed activation
        if user:
            Notification.objects.create(
                user=user,
                title="Account Activation Failed",
                message="The activation link is invalid or expired. Please try again."
            )

        messages.error(request, 'Activation link is invalid!')
        return redirect('register')




# def activate(request, uidb64, token):
#     try:
#         uid = force_str(urlsafe_base64_decode(uidb64))
#         user = User.objects.get(pk=uid)
#     except (TypeError, ValueError, OverflowError, User.DoesNotExist):
#         user = None

#     if user is not None and account_activation_token.check_token(user, token):
#         user.is_active = True
#         user.save()
#         login(request, user)
#         messages.success(request, 'Your account has been activated successfully!')
#         return redirect('login')
#     else:
#         messages.error(request, 'Activation link is invalid!')
#         return redirect('register')




@login_required
def profile(request):
    
    user = request.user
    books_count = get_user_books_count(user)
    download_count = Download.objects.filter(user=request.user).count()
    
    context = {
        'books_count': books_count,
        'download_count': download_count,
    }
    
    return render(request, 'user/profile.html', context)

# def user_login(request):
#     if request.method == 'POST':
#         username = request.POST['username']
#         password = request.POST['password']
#         user = authenticate(request, username=username, password=password)
#         if user is not None:
#             login(request, user)
#             messages.success(request, 'Login successful!')
#             return redirect('profile')  # Redirect to profile after login
#         else:
#             messages.error(request, 'Invalid credentials. Please try again.')
#     return render(request, 'user/login.html')


# def user_login(request):
#     if request.method == 'POST':
#         username = request.POST['username']
#         password = request.POST['password']
        
#         # Try to get the user first
#         try:
#             user = User.objects.get(username=username)
#         except User.DoesNotExist:
#             messages.error(request, 'Invalid credentials. Please try again.')
#             return render(request, 'user/login.html')

#         # Now authenticate
#         user = authenticate(request, username=username, password=password)

#         if user is not None:
#             if user.is_active:
#                 login(request, user)

#                 # Create a notification for successful login
#                 Notification.objects.create(
#                     user=user,
#                     title="Login Successful",
#                     message="You have logged in successfully."
#                 )

#                 messages.success(request, 'Login successful!')
#                 return redirect('profile')  # Redirect to profile after login
#             else:
#                 messages.error(request, 'Your account is not activated. Please check your email to activate your account.')
#                 return redirect('account_activation_sent')  # Redirect to account activation info page
#         else:
#             messages.error(request, 'Invalid credentials. Please try again.')

#             # Optionally, create a failed login notification for admin or security team
#             Notification.objects.create(
#                 user=None,  # Could be None for failed login attempt tracking
#                 title="Failed Login Attempt",
#                 message=f"Failed login attempt for username: {username}. This may require further investigation."
#             )

#     return render(request, 'user/login.html')


def user_login(request):
    # Get the 'next' parameter, or default to 'profile' if not provided
    next_page = request.GET.get('next', 'profile')  # Or specify a default redirect page

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        # Try to get the user first
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, 'Invalid credentials. Please try again.')
            return render(request, 'user/login.html')

        # Now authenticate
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)

                # Create a notification for successful login
                Notification.objects.create(
                    user=user,
                    title="Login Successful",
                    message="You have logged in successfully."
                )

                messages.success(request, 'Login successful!')

                # Redirect to the page the user was trying to access before login
                return redirect(next_page)  # Redirect to 'next' or profile if none specified
            else:
                messages.error(request, 'Your account is not activated. Please check your email to activate your account.')
                return redirect('account_activation_sent')  # Redirect to account activation info page
        else:
            messages.error(request, 'Invalid credentials. Please try again.')

            # Optionally, create a failed login notification for admin or security team
            Notification.objects.create(
                user=None,  # Could be None for failed login attempt tracking
                title="Failed Login Attempt",
                message=f"Failed login attempt for username: {username}. This may require further investigation."
            )

    return render(request, 'user/login.html')


# def user_login(request):
#     if request.method == 'POST':
#         username = request.POST['username']
#         password = request.POST['password']
        
#         # Try to get the user first
#         try:
#             user = User.objects.get(username=username)
#         except User.DoesNotExist:
#             messages.error(request, 'Invalid credentials. Please try again.')
#             return render(request, 'user/login.html')

#         # Now authenticate
#         user = authenticate(request, username=username, password=password)

#         if user is not None:
#             if user.is_active:
#                 login(request, user)
#                 messages.success(request, 'Login successful!')
#                 return redirect('profile')  # Redirect to profile after login
#             else:
#                 messages.error(request, 'Your account is not activated. Please check your email to activate your account.')
#                 return redirect('account_activation_sent')  # Redirect to an account activation info page
#         else:
#             messages.error(request, 'Invalid credentials. Please try again.')

#     return render(request, 'user/login.html')


def user_logout(request):
    # Optionally, create a notification when the user logs out
    if request.user.is_authenticated:
        Notification.objects.create(
            user=request.user,
            title="Logged Out",
            message="You have logged out successfully."
        )

    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')





# def user_logout(request):
#     logout(request)
#     messages.success(request, 'You have been logged out.')
#     return redirect('login')


# Create your views here.

# def contact_view(request):
#     if request.method == 'POST':
#         form = ContactForm(request.POST)
#         if form.is_valid():
#             # Process the form data (e.g., send an email)
#             form.save()  # Or any processing you need
#             messages.success(request, 'Your message has been sent successfully.')
#             response_data = {
#                 'success': True,
#                 'messages': ['Your message has been sent successfully.'],
#                 'form_html': render_to_string('partials/_contactsec.html', {'form': ContactForm()})
#             }
#             return JsonResponse(response_data)
#         else:
#             # Collect and send back error messages
#             for field, errors in form.errors.items():
#                 for error in errors:
#                     messages.error(request, error)
#             response_data = {
#                 'success': False,
#                 'form_html': render_to_string('partials/_contactsec.html', {'form': form})
#             }
#             return JsonResponse(response_data)
#     else:
#         form = ContactForm()  # Handle GET requests

#     return render(request, 'partials/_contactsec.html', {'form': form})


# def contact_view(request):
#     if request.method == 'POST':
#         form = ContactForm(request.POST)
#         if form.is_valid():
#             # Extract cleaned data from form
#             name = form.cleaned_data.get('firstname')
#             email = form.cleaned_data.get('email')
#             message = form.cleaned_data.get('message')

#             # Process the form data (e.g., send an email)
#             # Send email to admin
#             send_mail(
#                 subject=f"New Contact Message from {name}",
#                 message=message,
#                 from_email=email,
#                 recipient_list=['chill123@gmail.com'],  # Replace with actual admin email
#                 fail_silently=False,
#             )

#             # You could also add an auto-response to the sender if needed.
#             send_mail(
#                 subject="Thank you for contacting us",
#                 message="We have received your message and will get back to you shortly.",
#                 from_email='hello@example.com',  # Ensure this matches your DEFAULT_FROM_EMAIL
#                 recipient_list=[email],
#                 fail_silently=False,
#             )

#             # Save form data if necessary
#             form.save()  

#             # Send success message and updated form
#             messages.success(request, 'Your message has been sent successfully.')
#             response_data = {
#                 'success': True,
#                 'messages': ['Your message has been sent successfully.'],
#                 'form_html': render_to_string('partials/_contactsec.html', {'form': ContactForm()})
#             }
#             return JsonResponse(response_data)
#         else:
#             # Collect and send back error messages
#             for field, errors in form.errors.items():
#                 for error in errors:
#                     messages.error(request, error)
#             response_data = {
#                 'success': False,
#                 'form_html': render_to_string('partials/_contactsec.html', {'form': form})
#             }
#             return JsonResponse(response_data)
#     else:
#         form = ContactForm()  # Handle GET requests

#     return render(request, 'partials/_contactsec.html', {'form': form})


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Extract cleaned data from form
            name = form.cleaned_data.get('firstname')
            email = form.cleaned_data.get('email')
            message = form.cleaned_data.get('message')

            # Prepare the email content using the template
            email_content = render_to_string('user/emails/email_template.html', {
                'name': name,
                'email': email,
                'message': message,
            })

            # Send email to admin
            try:
                admin_email = EmailMessage(
                    subject=f"New Contact Message from {name}",
                    body=email_content,
                    from_email='hello@example.com',  # Replace with your email
                    to=['chill123@gmail.com'],  # Replace with actual admin email
                )
                admin_email.content_subtype = 'html'  # Send as HTML
                admin_email.send(fail_silently=False)

                # Send auto-response to the user (optional)
                auto_response_content = render_to_string('user/emails/auto_response_template.html', {
                    'name': name,
                    'message': message,
                })
                auto_response_email = EmailMessage(
                    subject="Thank you for contacting us",
                    body=auto_response_content,
                    from_email='hello@example.com',
                    to=[email],
                )
                auto_response_email.content_subtype = 'html'
                auto_response_email.send(fail_silently=False)

                # Optionally, save the form data to the database if needed
                form.save()  # Uncomment if you want to save the data

                # Success message and updated form
                messages.success(request, 'Your message has been sent successfully.')

                response_data = {
                    'success': True,
                    'messages': ['Your message has been sent successfully.'],
                    'form_html': render_to_string('partials/_contactsec.html', {'form': ContactForm()})
                }
                return JsonResponse(response_data)

            except Exception as e:
                # Handle exceptions during email sending
                messages.error(request, f"An error occurred while sending your message: {str(e)}")
                response_data = {
                    'success': False,
                    'messages': ['An error occurred while sending your message. Please try again later.'],
                    'form_html': render_to_string('partials/_contactsec.html', {'form': form})
                }
                return JsonResponse(response_data)

        else:
            # Collect and send back error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)

            response_data = {
                'success': False,
                'form_html': render_to_string('partials/_contactsec.html', {'form': form})
            }
            return JsonResponse(response_data)

    else:
        form = ContactForm()  # Handle GET requests

    return render(request, 'partials/_contactsec.html', {'form': form})


def about_us(request):
    return render(request, 'user/aboutus.html')

def services(request):
    return render(request, 'user/services.html')

def contact_us(request):
    return render(request, 'user/contactus.html')

def shop(request):
    books = Book.objects.all()
    categories = Category.objects.all()  # For displaying category filter
    featured_books = Book.objects.filter(is_featured=True)
    
    # Category Filter
    category_id = request.GET.get('category')
    if category_id:
        selected_category = get_object_or_404(Category, id=category_id)
        books = books.filter(categories=selected_category)
        
    
    # Free/Paid Filter
    free_filter = request.GET.get('free')
    if free_filter == 'true':
        books = books.filter(is_free=True)
    elif free_filter == 'false':
        books = books.filter(is_free=False)
        
        
    # Free/Paid Filter
    featured_filter = request.GET.get('featured')
    if featured_filter == 'true':
        books = books.filter(is_featured=True)
    elif featured_filter == 'false':
        books = books.filter(is_featured=False)


    # Search
    search_query = request.GET.get('q', '')
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(books, 12)  # Show 12 books per page
    page = request.GET.get('page')
    books = paginator.get_page(page)

    context = {
        'books': books,
        'categories': categories,
        'featured_books': featured_books,
        'search_query': search_query,
        'selected_category': category_id,
        'free_filter': free_filter,
    }
    
    return render(request, 'user/shop.html', context)



def user_notifications(request):
    return render(request, 'user/user_notifications.html')




def contact_support(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Extract cleaned data from form
            name = form.cleaned_data.get('firstname')
            email = form.cleaned_data.get('email')
            message = form.cleaned_data.get('message')

            # Prepare the email content using the template
            email_content = render_to_string('user/emails/email_template.html', {
                'name': name,
                'email': email,
                'message': message,
            })

            try:
                # Send email to admin
                admin_email = EmailMessage(
                    subject=f"New Contact Message from {name}",
                    body=email_content,
                    from_email='hello@example.com',  # Replace with your email
                    to=['chill123@gmail.com'],  # Replace with actual admin email
                )
                admin_email.content_subtype = 'html'  # Send as HTML
                admin_email.send(fail_silently=False)

                # Send auto-response to the user
                auto_response_content = render_to_string('user/emails/auto_response_template.html', {
                    'name': name,
                    'message': message,
                })
                auto_response_email = EmailMessage(
                    subject="Thank you for contacting us",
                    body=auto_response_content,
                    from_email='hello@example.com',
                    to=[email],
                )
                auto_response_email.content_subtype = 'html'
                auto_response_email.send(fail_silently=False)

                # Optionally, save the form data if needed
                form.save()  # Uncomment if you want to save the data

                # Success message and redirection
                messages.success(request, 'Your message has been sent successfully.')
                return redirect('profile')  # Redirect to a success page or profile page

            except Exception as e:
                # Handle any exceptions that occur during email sending
                messages.error(request, f"An error occurred while sending your message: {str(e)}")
                return render(request, 'partials/_contactform.html', {'form': form})

        else:
            # Collect and send back error messages from the form
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)

    else:
        form = ContactForm()  # Handle GET requests

    return render(request, 'partials/_contactform.html', {'form': form})




def account_activation_sent(request):
    messages.info(request, "You need to activate your account. An email has been sent to your email address.")
    return render(request, 'user/account_activation_sent.html')


# from django.core.mail import EmailMessage
# from django.template.loader import render_to_string

# def send_html_email(request):
#     subject = "HTML Test Email from Django"
#     html_content = render_to_string('email_template.html', {'name': 'John Doe'})
#     email = EmailMessage(subject, html_content, 'your_email@gmail.com', ['recipient@example.com'])
#     email.content_subtype = 'html'  # Set the content type to HTML
#     email.send(fail_silently=False)
#     return HttpResponse("HTML email sent successfully!")

@login_required
def user_orders(request):
    # Fetch orders for the authenticated user
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'user/user_orders.html', {'orders': orders})





















