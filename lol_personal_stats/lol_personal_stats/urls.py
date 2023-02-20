from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('mastery_points_app/', include('mastery_points_app.urls')),
    path('admin/', admin.site.urls),
]