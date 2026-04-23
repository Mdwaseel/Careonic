import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthcare_mini.settings')
django.setup()

from django.contrib.auth.models import User
from app.models import DoctorProfile

def create_doctors():
    doctors_data = [
        {"username": "drsmith", "password": "password123", "first_name": "John", "last_name": "Smith", "specialty": "Cardiologist"},
        {"username": "drjane", "password": "password123", "first_name": "Jane", "last_name": "Doe", "specialty": "General Physician"},
        {"username": "drhouse", "password": "password123", "first_name": "Gregory", "last_name": "House", "specialty": "Endocrinologist"}
    ]
    
    for data in doctors_data:
        if not User.objects.filter(username=data["username"]).exists():
            user = User.objects.create_user(
                username=data["username"],
                password=data["password"],
                first_name=data["first_name"],
                last_name=data["last_name"]
            )
            DoctorProfile.objects.create(
                user=user,
                specialty=data["specialty"]
            )
            print(f"Created doctor: {data['username']} ({data['specialty']})")
        else:
            print(f"Doctor {data['username']} already exists.")

if __name__ == "__main__":
    create_doctors()
