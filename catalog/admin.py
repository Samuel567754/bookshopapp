from django.contrib import admin
from .models import Book, Category
from django.utils.html import format_html


# Customizing the BookAdmin
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'display_categories', 'final_price', 'is_free', 'stock', 'display_image','is_featured', 'display_file')  
    search_fields = ('title', 'author', 'description')  # Enable search by title, author, and description
    list_filter = ('categories', 'is_free', 'price','is_featured')  # Filter by categories, price, is_free status
    ordering = ('-title',)  # Order by title by default
    actions = ['mark_as_free', 'mark_as_paid']  # Custom actions to toggle free/paid status
    filter_horizontal = ('categories',)  # Horizontal filter for many-to-many relationships
    readonly_fields = ('final_price',)  # Make the final_price field read-only in the admin

    # Function to display categories as comma-separated values
    def display_categories(self, obj):
        return ", ".join(category.name for category in obj.categories.all())
    display_categories.short_description = 'Categories'

    # Method to display image thumbnail in admin
    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="auto" />', obj.image.url)
        return "(No image)"
    display_image.short_description = 'Image'

    # Function to display the download link for the book file
    def display_file(self, obj):
        if obj.file:
            return format_html('<a href="{}" download>Download File</a>', obj.file.url)
        return "(No file available)"
    display_file.short_description = 'File'

    # Custom action to mark books as free
    def mark_as_free(self, request, queryset):
        queryset.update(is_free=True, price=0.00)
        self.message_user(request, f"{queryset.count()} books marked as free.")
    mark_as_free.short_description = 'Mark selected books as free'

    # Custom action to mark books as paid
    def mark_as_paid(self, request, queryset):
        queryset.update(is_free=False)
        self.message_user(request, f"{queryset.count()} books marked as paid.")
    mark_as_paid.short_description = 'Mark selected books as paid'


# Customizing the CategoryAdmin
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)  # Show category name
    search_fields = ('name',)  # Enable search by category name

# Inline model to allow editing books within categories
class BookInline(admin.TabularInline):
    model = Book.categories.through  # Many-to-many through relation for inline editing
    extra = 1  # Number of empty forms to display

# Custom CategoryAdmin with inline Book model
class CategoryAdminWithBooks(CategoryAdmin):
    inlines = [BookInline]  # Add inline to allow editing books in category admin


# Registering the models and customized admin classes
admin.site.register(Book, BookAdmin)
admin.site.register(Category, CategoryAdminWithBooks)


