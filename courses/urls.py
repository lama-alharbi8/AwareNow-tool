from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Platform Admin URLs
    path('platform-admin/', views.platform_admin_dashboard, name='platform_admin_dashboard'),
    path('platform-admin/courses/create/', views.create_course, name='create_course'),
    path('platform-admin/courses/<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('platform-admin/courses/<int:course_id>/assign/', views.assign_course_to_companies, name='assign_course_to_companies'),
]