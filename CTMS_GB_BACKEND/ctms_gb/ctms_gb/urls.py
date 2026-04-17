from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("transport.urls")),
    path("api/auth/", include("users.urls")),
    path("api/tickets/", include("passenger_tickets.urls")),
    path("api/checkout/", include("Payment.urls")),
    path("api/contact/", include("contact.urls")),
    path('api/about/', include('about.urls')),

]
set
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

