# user/context_processors.py (or the appropriate path where your context processors are located)
from .models import WishList

def wishlist_count(request):
    wishlist_count = 0

    if request.user.is_authenticated:
        # Get the user's wishlist and count the items in it
        wishlist, created = WishList.objects.get_or_create(user=request.user)
        wishlist_count = wishlist.books.count()

    return {'wishlist_count': wishlist_count}
