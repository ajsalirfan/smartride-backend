# ============================================================
# 🚀 SMART RIDE PROJECT — URL CONFIGURATION (CUSTOM ADMIN ✅)
# ============================================================

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

# JWT Token Refresh
from rest_framework_simplejwt.views import TokenRefreshView

# Custom Admin
from Admin.admin import smartride_admin_site


# Health check endpoint
def health(request):
    return JsonResponse({'status': 'ok', 'service': 'SmartRide Backend Active ✅'})


# Main API Root
@api_view(['GET'])
def main_api_root(request):
    return Response({
        'smart-ride-admin': '/smartride-admin/',
        'django-admin': '/admin/',
        'users-api': '/api/Users/',
        'staff-api': '/api/StaffWork/',
        'admin-api': '/api/Admin/',
        'health-check': '/health/',
    })


urlpatterns = [
    path('', main_api_root, name='main-api-root'),

    # Custom Admin
    path('smartride-admin/', smartride_admin_site.urls),

    # Default Admin
    path('admin/', admin.site.urls),

    # JWT Refresh
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # App URLs
    path('api/Users/', include('Users.urls')),
    path('api/StaffWork/', include('StaffWork.urls')),
    path('api/Admin/', include('Admin.urls')),
    path('health/', health),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
