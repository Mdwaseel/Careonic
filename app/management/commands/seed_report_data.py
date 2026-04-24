from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import BPMeasurement, WeightLog, DietLog, SymptomLog
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = "Seeds random health data for patient01 for the last 30 days to demonstrate reports."

    def handle(self, *args, **kwargs):
        username = "patient01"
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User {username} does not exist. Run seed_patients first."))
            return

        self.stdout.write(f"Generating data for {username}...")

        # Clear existing data for this user to avoid duplicates
        BPMeasurement.objects.filter(user=user).delete()
        WeightLog.objects.filter(user=user).delete()
        DietLog.objects.filter(user=user).delete()
        SymptomLog.objects.filter(user=user).delete()

        today = date.today()
        
        for i in range(30):
            current_date = today - timedelta(days=30 - i - 1)
            
            # BP Measurement
            BPMeasurement.objects.create(
                user=user,
                measurement_date=current_date,
                systolic_bp=random.randint(110, 135),
                diastolic_bp=random.randint(70, 88),
                heart_rate=random.randint(65, 95),
                notes="Feeling normal." if random.random() > 0.2 else "Slight headache."
            )
            
            # Weight Log
            # Start around 70kg, varying slightly
            weight = round(70.0 + random.uniform(-1.5, 1.5), 1)
            WeightLog.objects.create(
                user=user,
                log_date=current_date,
                weight=weight
            )
            
            # Diet Log
            DietLog.objects.create(
                user=user,
                log_date=current_date,
                sodium_intake=random.randint(1800, 2400),
                potassium_intake=random.randint(2800, 3200),
                carb_intake=random.randint(220, 280)
            )
            
            # Symptom Log (not every day, maybe 30% of days)
            if random.random() < 0.3:
                severities = ['Mild', 'Moderate', 'Severe']
                symptoms = ['Headache', 'Fatigue', 'Dizziness', 'Nausea']
                SymptomLog.objects.create(
                    user=user,
                    log_date=current_date,
                    symptom_description=random.choice(symptoms),
                    severity=random.choices(severities, weights=[0.6, 0.3, 0.1])[0]
                )

        self.stdout.write(self.style.SUCCESS(f"Successfully generated 30 days of data for {username}!"))
