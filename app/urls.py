# project/urls.py

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from app import views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Public / Auth
    path('', views.index, name='index'),
    path('user_login/', views.user_login, name='user_login'),
    path('logout/', views.log_out, name='log_out'),

    # Registration
    path('register/', views.choose_registration, name='register'),
    path('register/college/', views.college_register, name='college_register'),
    path('register/university/', views.university_register, name='university_register'),

    # College dashboards
    path('college_dashboard/', views.college_dashboard, name='college_dashboard'),
    path('college/assigned-papers/', views.college_assigned_papers, name='college_assigned_papers'),
    path('request-aes-key/<int:paper_id>/', views.request_aes_key, name='request_aes_key'),

    # University dashboards
    path('university_dashboard/', views.university_dashboard, name='university_dashboard'),
    path('colleges/', views.college_list_view, name='college_list'),
    path('papers/', views.uploaded_papers_view, name='uploaded_papers'),
    path('papers/view/<int:paper_id>/', views.view_encrypted_pdf, name='view_encrypted_pdf'),

    # Key‐request workflow
    path('view-key-requests/', views.view_key_requests, name='view_key_requests'),
    path('print_encrypted_pdf/<int:paper_id>/', views.print_encrypted_pdf, name='print_encrypted_pdf'),
    path('print/<int:paper_id>/', views.print_encrypted_pdf, name='print_encrypted_pdf'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
