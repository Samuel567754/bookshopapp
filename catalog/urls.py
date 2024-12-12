from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.book_list, name='book_list'),  # List all books
    # path('featured/', views.featured_books, name='featured_books'),  # URL for featured books
    # path('books/', views.all_books, name='all_books'),  # URL for all books
    path('books/<int:pk>/', views.book_detail, name='book_detail'),  # URL for individual book detail
    path('books/category/<str:category_name>/', views.books_by_category, name='books_by_category'),  # Filter by category
    path('books/<int:book_id>/download/', views.download_book, name='download_book'),  # Book download after purchase
    path('download/<int:pk>/', views.downloadpage, name='downloadpage'),
]


