from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.exceptions import ValidationError

# Doctor Model
class Doctor(AbstractUser):
    is_master_doctor = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    

# Patient Model
class Patient(models.Model):
    first_name = models.CharField('Imie', max_length=100)
    last_name = models.CharField('Nazwisko',max_length=100)
    dob = models.DateField('Data urodzenia', blank=True)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+489999999'. Up to 15 digits allowed.")
    phone_number = models.CharField('Numer telefonu', validators=[phone_regex], max_length=17) # Validators should be a list
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='patients', verbose_name='Lekarz')
    city = models.CharField('Miasto', max_length=100, default='Kielce', blank=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['first_name', 'last_name'], name='unique_client_name')
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if Patient.objects.filter(first_name=self.first_name, last_name=self.last_name).exists():
            raise ValidationError(f"Pacjent {self.first_name} {self.last_name} juz istnieje.")
        super(Patient, self).save(*args, **kwargs)

# Appointment Model
class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments', verbose_name='Pacjent')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments', verbose_name='Lekarz')
    date = models.DateTimeField('Data')
    time = models.TimeField('Godzina') 
    duration = models.DurationField('Czas Trwania')
    reason = models.TextField('Powod')
    money = models.DecimalField('Zaplata', decimal_places=2, max_digits=10)
    city = models.CharField('Miasto', max_length=100, default='Kielce', blank=True)
    

    def __str__(self):
        return f"{self.patient} od doktora {self.doctor} z wizyta w dniu {self.date} o godzinie {self.time}"