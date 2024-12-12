from django.contrib import admin
from django.urls import path, include
# from django.conf.urls import url

from django.conf import settings
from django.conf.urls.static import static
import os
from django.contrib.auth import views as auth_views
from django.conf.urls.i18n import set_language



urlpatterns = [
    # url(r'^i18n/', include('django.conf.urls.i18n')),  # Add this line
    path('admin/', admin.site.urls),
    path('', include('catalog.urls')),
    path('order/', include('order.urls')),
    path('cart/' , include('cart.urls')),
    path('user/' , include('user.urls')),
    path('notifications/', include('notifications.urls')),
    
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

