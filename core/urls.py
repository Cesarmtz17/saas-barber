from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Página de inicio del SaaS (landing page)
    path('', views.home_view, name='home'),
    
    # Redirección después del login
    path('login-redirect/', views.login_redirect_view, name='login_redirect'),
    
    # Rutas por negocio (cada negocio tiene su propia página web)
    path('<slug:business_slug>/', views.client_booking_view, name='business_home'),
    path('<slug:business_slug>/crear/', views.create_appointment, name='create_appointment'),
    path('<slug:business_slug>/api/slots/', views.get_available_slots_api, name='get_available_slots_api'),
    path('<slug:business_slug>/dashboard/', views.dashboard_view, name='dashboard'),
    path('<slug:business_slug>/dashboard/api/appointments/', views.get_dashboard_appointments_api, name='dashboard_appointments_api'),
    path('<slug:business_slug>/dashboard/cita/<int:appointment_id>/actualizar/', views.update_appointment_status, name='update_appointment_status'),
    path('<slug:business_slug>/dashboard/bloquear-horario/', views.block_time_view, name='block_time'),
    path('<slug:business_slug>/dashboard/crear-cita/', views.create_appointment_manual_view, name='create_appointment_manual'),
    path('<slug:business_slug>/dashboard/editar-sitio/', views.edit_site_view, name='edit_site'),
    path('<slug:business_slug>/dashboard/api/update-field/', views.update_business_field_api, name='update_business_field_api'),
    path('<slug:business_slug>/dashboard/api/upload-image/', views.upload_gallery_image, name='upload_gallery_image'),
    path('<slug:business_slug>/dashboard/api/delete-image/<int:image_id>/', views.delete_gallery_image, name='delete_gallery_image'),
    
    # Rutas para clientes (sin negocio específico)
    path('mis-reservas/', views.my_appointments_view, name='my_appointments'),
    
    # Rutas legacy (redirigen a la nueva estructura)
    path('reserva/<slug:business_slug>/', views.client_booking_view, name='client_booking'),
]
