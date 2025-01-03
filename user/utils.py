
from order.models import Order, OrderItem
from catalog.models import Book
import openai
from django.conf import settings

def get_user_purchased_books(user):
    # Filter for completed orders by the user
    completed_orders = Order.objects.filter(user=user, status='completed')
    
    # Retrieve books from these orders
    books = Book.objects.filter(orderitem__order__in=completed_orders).distinct()
    
    return books

def get_user_books_count(user):
    # Get all completed orders for the user
    completed_orders = Order.objects.filter(user=user, status='completed')
    
    # Count the total number of unique books purchased in those orders
    total_books_count = OrderItem.objects.filter(order__in=completed_orders).count()
    
    return total_books_count  # Returns the count of books purchased



# def get_chatgpt_response(prompt):
#     openai.api_key = settings.OPENAI_API_KEY
#     try:
#         response = openai.ChatCompletion.create(
#             model="gpt-3.5-turbo",
#             messages=[{"role": "user", "content": prompt}],
#         )
#         return response['choices'][0]['message']['content']
#     except Exception as e:
#         return f"Error: {str(e)}"


def get_chatgpt_response(prompt):
    """
    Fetches a response from OpenAI's GPT-4 model for a given prompt.
    """
    openai.api_key = settings.OPENAI_API_KEY
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Use the GPT-4 model
            store=True,
            messages=[{"role": "user", "content": prompt}],
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error: {str(e)}"