from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('signup/', views.sign_up, name='signup'),
    path('logout/', views.user_logout, name='logout'),
    path('appointments/', views.appointments_view, name='appointments'),
    path('appointments/create/', views.create_appointment, name='create_appointment'),
    path('patient/create/', views.create_patient, name='create_patient'),
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/<int:pk>/', views.patient_detail, name='patient_detail'),
    path('doctors/', views.doctor_list_view, name='doctor_list'),
    path('doctors/<int:doctor_id>/', views.doctor_detail_view, name='doctor_detail'),
    # path('calendar/', views.calendar_view, name='calendar_view')
    
]