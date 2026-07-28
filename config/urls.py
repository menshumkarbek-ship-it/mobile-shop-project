from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # 🌐 Built-in Django route to handle language-switching form submissions
    path('i18n/', include('django.conf.urls.i18n')),

    # 🏪 Shop Application URLs
    path('', include('shop.urls', namespace='shop')),
]

# Serve media files locally during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)