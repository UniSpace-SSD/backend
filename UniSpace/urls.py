from django.contrib import admin
from django.urls import path, include
import rest_framework.schemas
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

API_TITLE = 'UniSpace API'
API_DESCRIPTION = 'UniSpace API'

schema_view = get_schema_view(
    openapi.Info(
        title=API_TITLE,
        description=API_DESCRIPTION,
        default_version='v1',
        terms_of_service='https://www.google.com/policies/terms/',
        contact=openapi.Contact(email='email@unispace.org'),
        license=openapi.License(name='BSD License')
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('swagger.<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path(
        'schema/',
        rest_framework.schemas.get_schema_view(
            title=API_TITLE,
            description=API_DESCRIPTION
        ),
        name='openapi-schema'
    ),

    # Endpoint Auth
    path('api/auth/', include('dj_rest_auth.urls')),                # Login, Logout, Password Reset
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')), # Registrazione

    path('api/', include('spaces.urls')),
    path('api/', include('reservations.urls')),     
]
