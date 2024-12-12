from django.db import models

# Category Model
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

# Book Model
class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_free = models.BooleanField(default=False)
    # download_link = models.URLField()  # Assuming books are hosted online
    file = models.FileField(upload_to='books/', null=True, blank=True)  # File field to store the actual book file
    stock = models.PositiveIntegerField(default=0)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    categories = models.ManyToManyField(Category, related_name='books')
    image = models.ImageField(upload_to='book_images/', null=True, blank=True)
     # New field to mark the book as featured
    is_featured = models.BooleanField(default=False)


    def __str__(self):
        return self.title

    def final_price(self):
        """Returns the price after discount if applicable."""
        return self.discount_price if self.discount_price else self.price
