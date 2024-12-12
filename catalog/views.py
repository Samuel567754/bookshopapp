from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from .models import Book, Category
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
# Add pagination and search to book_list
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Book
from notifications.models import Notification


def book_list(request):
    books = Book.objects.all()
    categories = Category.objects.all()  # For displaying category filter
    
    featured_books = Book.objects.filter(is_featured=True)
    
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
    }
    return render(request, 'catalog/book_list.html', context)
    

# List of books filtered by category
def books_by_category(request, category_name):
    category = get_object_or_404(Category, name=category_name)
    books_list = category.books.all()  # Retrieve all books related to the category
    paginator = Paginator(books_list, 10)  # Show 10 books per page

    page_number = request.GET.get('page')
    books = paginator.get_page(page_number)

    categories = Category.objects.all()  # To display all categories
    context = {
        'books': books,
        'category': category,
        'categories': categories,
    }
    return render(request, 'catalog/books_by_category.html', context)


# Book detail view
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    rating_range = list(range(1, 6))  # Creates a list [1, 2, 3, 4, 5]
    context = {
        'book': book,
        'rating_range': rating_range,
    }
    return render(request, 'catalog/book_detail.html', context)

# Download a book after purchase (or free download for free books)
@login_required
def download_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    
    if book.is_free or request.user.has_purchased(book):
        if book.file:
            response = HttpResponse(book.file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename={book.file.name}'
            return response
        else:
            return HttpResponse("No file found.")
    else:
        return HttpResponse("You need to purchase the book before downloading.")

# Helper method to simulate purchase (this method is not in the final application, just for example)
def has_purchased(user, book):
    # This method would ideally check if the user has purchased the book in real implementation
    # For now, we'll assume it always returns False
    return False

# download view
# @login_required
# def downloadpage(request, pk):
#     book = get_object_or_404(Book, pk=pk)
    
#     has_purchased_status = has_purchased(request.user, book)  # Use the standalone function here
#     context = {
#         'book': book,
#         'has_purchased_status': has_purchased_status,       
#     }
#     return render(request, 'catalog/downloadpage.html', context)



@login_required
def downloadpage(request, pk):
    book = get_object_or_404(Book, pk=pk)
    
    has_purchased_status = has_purchased(request.user, book)  # Assuming you have this function
    
    # Create a notification
    if has_purchased_status:
        notification_title = "Download Available"
        notification_message = f"You have already purchased the book '{book.title}'. You can download it now."
    else:
        notification_title = "Purchase Required"
        notification_message = f"You need to purchase the book '{book.title}' before downloading."
    
    # Save notification to the database
    notification = Notification.objects.create(
        user=request.user,
        title=notification_title,
        message=notification_message,
        is_read=False
    )

    # Get all notifications for the user
    notifications = Notification.objects.filter(user=request.user)

    # Pass the context to the template
    context = {
        'book': book,
        'has_purchased_status': has_purchased_status,
        'notifications': notifications,  # Include notifications in context
    }
    return render(request, 'catalog/downloadpage.html', context)