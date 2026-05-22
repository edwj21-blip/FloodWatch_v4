from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

admin.site.site_header = "FloodWatch Admin"
admin.site.site_title = "FloodWatch Admin Portal"
admin.site.index_title = "Flood Management Dashboard"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
