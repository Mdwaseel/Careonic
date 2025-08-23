from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    height = models.DecimalField(max_digits=5, decimal_places=2)
    initial_weight = models.DecimalField(max_digits=5, decimal_places=2)
    chronic_disease = models.CharField(max_length=50, default='Hypertension')
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], null=True, blank=True)

class BPMeasurement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    measurement_date = models.DateField()
    systolic_bp = models.IntegerField()
    diastolic_bp = models.IntegerField()
    heart_rate = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

class WeightLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    log_date = models.DateField()
    weight = models.DecimalField(max_digits=5, decimal_places=2)

class DietLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    log_date = models.DateField()
    sodium_intake = models.IntegerField()  # mg/day
    potassium_intake = models.IntegerField()  # mg/day
    carb_intake = models.IntegerField()  # grams/day

class SymptomLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    log_date = models.DateField()
    symptom_description = models.TextField()
    severity = models.CharField(max_length=10, choices=[('Mild', 'Mild'), ('Moderate', 'Moderate'), ('Severe', 'Severe')])