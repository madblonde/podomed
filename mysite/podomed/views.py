
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout 
from .forms import *
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from django.db.models import Q
from .models import Appointment, Patient
from django.http import HttpResponse
from django.http import JsonResponse
from django.utils.dateformat import format
from datetime import datetime
from django.views import generic
from django.utils.safestring import mark_safe
from calendar import HTMLCalendar
from django.contrib import messages

# class AppointmentCalendar(HTMLCalendar):
#     def __init__(self, appointments):
#         super().__init__()
#         self.appointments = appointments

#     def formatday(self, day, weekday):
#         appointments_on_day = self.appointments.filter(date__day=day)
#         appointments_html = '<ul>'
#         for appointment in appointments_on_day:
#             appointments_html += f'<li>{appointment.time.strftime("%H:%M")} - {appointment.patient.first_name} {appointment.patient.last_name}</li>'
#         appointments_html += '</ul>'

#         if day != 0:
#             return f"<td class='{self.cssclasses[weekday]}'><span class='day'>{day}</span>{appointments_html}</td>"
#         return '<td></td>'

#     def formatweek(self, theweek):
#         week_html = ''
#         for d, weekday in theweek:
#             week_html += self.formatday(d, weekday)
#         return f'<tr>{week_html}</tr>'

#     def formatmonth(self, year, month, withyear=True):
#         appointments = self.appointments.filter(date__year=year, date__month=month)
#         self.appointments = appointments

#         cal = f'<table class="calendar">\n'
#         cal += f'{self.formatmonthname(year, month, withyear=withyear)}\n'
#         cal += f'{self.formatweekheader()}\n'
#         for week in self.monthdays2calendar(year, month):
#             cal += f'{self.formatweek(week)}\n'
#         cal += '</table>'
#         return cal


# def calendar_view(request):
#     today = datetime.today()
#     appointments = Appointment.objects.all()
#     calendar = AppointmentCalendar(appointments)
#     html_calendar = calendar.formatmonth(today.year, today.month)

#     context = {
#         'calendar': mark_safe(html_calendar),
#         'today': today,
#     }
#     return render(request, 'podomed/calendar_view.html', context)


@csrf_protect
@login_required
def patient_list(request):
    query = request.GET.get('q')
    selected_city = request.GET.get('city', None)
    if query:
        patients = Patient.objects.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query)
        ).filter(doctor=request.user)
    else:
        patients = Patient.objects.filter(doctor=request.user)
    
    if selected_city:
        patients = patients.filter(city=selected_city)
    
    cities = Patient.objects.values_list('city', flat=True).distinct()
    return render(request, 'podomed/patient_list.html', {'patients': patients, 'cities': cities})

@csrf_protect
@login_required
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    appointments = Appointment.objects.filter(patient=patient).order_by('date', 'time')
    return render(request, 'podomed/patient_detail.html', {'patient': patient, 'appointments': appointments})

@csrf_protect
@login_required
def create_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.doctor = request.user  # Assign the logged-in doctor
            appointment.save()
            return redirect('/podomed/appointments')  # Redirect to the appointment list or detail page
    else:
        form = AppointmentForm()
    
    return render(request, 'podomed/create_appointment.html', {'form': form})

@csrf_protect
@login_required
def create_patient(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.doctor = request.user  # Assign the logged-in doctor
            patient.save()
            return redirect('/podomed/appointments')  # Redirect to the appointment list or detail page
    else:
        form = PatientForm()
    
    return render(request, 'podomed/create_patient.html', {'form': form})

@login_required
def appointments_view(request):
    # Get current date and week
    today = timezone.now().date()
    start_of_week = today - timezone.timedelta(days=today.weekday())  # Monday of current week
    end_of_week = start_of_week + timezone.timedelta(days=6)          # Sunday of current week

    # Filters
    selected_city = request.GET.get('city', None)
    selected_date = request.GET.get('date', None)
    selected_reason = request.GET.get('reason', None)
    filter_type = request.GET.get('filter', 'all')

    appointments = Appointment.objects.all()

    # Apply filter based on the selected tab (Today, This Week, All Appointments)
    if filter_type == 'today':
        appointments = appointments.filter(date__date=today)
    elif filter_type == 'this_week':
        appointments = appointments.filter(date__date__range=[start_of_week, end_of_week])

    # Filter by city if selected
    if selected_city:
        appointments = appointments.filter(city=selected_city)

    # Filter by date if provided
    if selected_date:
        appointments = appointments.filter(date__date=selected_date)

    # Filter by reason if provided
    if selected_reason:
        appointments = appointments.filter(reason__icontains=selected_reason)

    # Get unique cities and reasons for filtering
    cities = Appointment.objects.values_list('city', flat=True).distinct()
    reasons = Appointment.objects.values_list('reason', flat=True).distinct()

    # Calculate total earnings
    total_earnings = appointments.aggregate(total=models.Sum('money'))['total'] or 0

    context = {
        'appointments': appointments,
        'cities': cities,
        'reasons': reasons,
        'selected_city': selected_city,
        'selected_reason': selected_reason,
        'selected_date': selected_date,
        'filter_type': filter_type,
        'total_earnings': total_earnings,
    }

    return render(request, 'podomed/home.html', context)

# login page
@csrf_protect
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(username=username,password=password)
        if user is not None:
            login(request,user)
            return redirect("/podomed/appointments")
        else:
            messages.error(request, 'Invalid username or password')  # Add error message
            return redirect('/podomed/login')

    return render(request=request, template_name="registration/login.html", context={})

def sign_up(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.last_name = form.cleaned_data.get('last_name')
            if user.last_name == 'Gaik' or user.last_name == 'Jaros':
                user.is_master_doctor = True
            
            user.save()
            login(request, user)
            return redirect('/podomed/appointments')  # Replace 'dashboard' with your desired redirect URL name
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

# logout page
def user_logout(request):
    logout(request)
    return redirect('login')

# Helper function to check if the user is a master doctor
def is_master_doctor(user):
    return user.is_authenticated and user.is_master_doctor  # Assuming you have an `is_master_doctor` field in your model

@user_passes_test(is_master_doctor)
def doctor_list_view(request):
    doctors = Doctor.objects.exclude(id=request.user.id)  # Exclude the logged-in doctor
    return render(request, 'podomed/doctor_list.html', {'doctors': doctors})

@user_passes_test(is_master_doctor)
def doctor_detail_view(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)

    # Handling search for clients
    client_query = request.GET.get('patient_search', '')
    clients = doctor.patients.all()
    if client_query:
        clients = clients.filter(Q(first_name__icontains=client_query) | Q(last_name__icontains=client_query))

    # Handling filtering of appointments by date
    filter_date = request.GET.get('filter_date', '')
    appointments = doctor.appointments.all()
    if filter_date:
        appointments = appointments.filter(date=filter_date)

    total_earnings = appointments.aggregate(total=models.Sum('money'))['total'] or 0

    return render(request, 'podomed/doctor_detail.html', {
        'doctor': doctor,
        'clients': clients,
        'appointments': appointments,
        'total_earnings': total_earnings,
        'client_query': client_query,
        'filter_date': filter_date
    })