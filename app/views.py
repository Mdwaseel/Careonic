from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import UserProfile, BPMeasurement, WeightLog, DietLog, SymptomLog
from django.utils import timezone
from django.db.models import Avg
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from datetime import timedelta, date
from django.http import JsonResponse
from django.views.decorators.http import require_GET
import logging
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .forms import BPForm, WeightForm, DietForm, SymptomForm, UserProfileForm
from datetime import datetime
import json
from django.db.models import Avg, Count
import matplotlib.pyplot as plt
import io
import base64
from dateutil.relativedelta import relativedelta
from dateutil.relativedelta import relativedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import matplotlib
matplotlib.use('Agg')  # ✅ Fix for Django environment
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

def signup(request):
    if request.method == "POST":
        user_form = UserCreationForm(request.POST)
        profile_form = UserProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            login(request, user)  # Auto login after signup
            return redirect('dashboard')
    else:
        user_form = UserCreationForm()
        profile_form = UserProfileForm()

    return render(request, 'app/signup.html', {
        'form': user_form,
        'profile_form': profile_form
    })

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'app/login.html', {'form': form})

@login_required
def dashboard(request):
    # Get dates with entries for calendar highlighting
    entries = BPMeasurement.objects.filter(user=request.user).values_list('measurement_date', flat=True).distinct()
    event_dates = [d.strftime('%Y-%m-%d') for d in entries]
    return render(request, 'app/dashboard.html', {'event_dates': json.dumps(event_dates)})

@login_required
def bp_tracking(request):
    today = date.today().strftime('%Y-%m-%d')

    if request.method == 'POST':
        # ✅ Handle BP
        if request.POST.get('systolic_bp') and request.POST.get('diastolic_bp'):
            bp_form = BPForm({
                'measurement_date': request.POST.get('bp_measurement_date'),
                'systolic_bp': request.POST.get('systolic_bp'),
                'diastolic_bp': request.POST.get('diastolic_bp'),
                'heart_rate': request.POST.get('heart_rate'),
                'notes': request.POST.get('bp_notes'),
            })
            if bp_form.is_valid():
                bp = bp_form.save(commit=False)
                bp.user = request.user
                bp.save()

        # ✅ Handle Weight
        if request.POST.get('weight'):
            weight_form = WeightForm({
                'log_date': request.POST.get('weight_date') or date.today(),   # fixed
                'weight': request.POST.get('weight'),
            })
            if weight_form.is_valid():
                w = weight_form.save(commit=False)
                w.user = request.user
                w.save()

        # ✅ Handle Diet
        if request.POST.get('sodium_intake') or request.POST.get('potassium_intake') or request.POST.get('carb_intake'):
            diet_form = DietForm({
                'log_date': request.POST.get('diet_date'),   # fixed
                'sodium_intake': request.POST.get('sodium_intake'),
                'potassium_intake': request.POST.get('potassium_intake'),
                'carb_intake': request.POST.get('carb_intake'),
            })
            if diet_form.is_valid():
                d = diet_form.save(commit=False)
                d.user = request.user
                d.save()

        # ✅ Handle Symptom
        if request.POST.get('symptom_description'):
            symptom_form = SymptomForm({
                'log_date': request.POST.get('symptom_date'),   # fixed
                'symptom_description': request.POST.get('symptom_description'),
                'severity': request.POST.get('severity'),
            })
            if symptom_form.is_valid():
                s = symptom_form.save(commit=False)
                s.user = request.user
                s.save()

        messages.success(request, "All valid data logged successfully!")
        return redirect('bp_tracking')

    # load recent logs
    measurements = BPMeasurement.objects.filter(user=request.user).order_by('-measurement_date')[:5]
    weight_logs = WeightLog.objects.filter(user=request.user).order_by('-log_date')[:5]
    diet_logs = DietLog.objects.filter(user=request.user).order_by('-log_date')[:5]
    symptom_logs = SymptomLog.objects.filter(user=request.user).order_by('-log_date')[:5]

    return render(request, 'app/bp_tracking.html', {
        'measurements': measurements,
        'weight_logs': weight_logs,
        'diet_logs': diet_logs,
        'symptom_logs': symptom_logs,
        'today': today,
    })


@login_required
@require_GET
def get_entry_details(request, date):
    try:
        logger.info(f"Fetching details for date: {date}")
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        bp_entries = BPMeasurement.objects.filter(user=request.user, measurement_date=date_obj).count()
        weight_entries = WeightLog.objects.filter(user=request.user, log_date=date_obj).count()
        diet_entries = DietLog.objects.filter(user=request.user, log_date=date_obj).count()
        symptom_entries = SymptomLog.objects.filter(user=request.user, log_date=date_obj).count()

        details_list = []
        if bp_entries > 0:
            details_list.append(f"<li>{bp_entries} BP measurement(s)</li>")
        if weight_entries > 0:
            details_list.append(f"<li>{weight_entries} weight log(s)</li>")
        if diet_entries > 0:
            details_list.append(f"<li>{diet_entries} diet log(s)</li>")
        if symptom_entries > 0:
            details_list.append(f"<li>{symptom_entries} symptom log(s)</li>")

        if details_list:
            details = "<ul>" + "".join(details_list) + "</ul>"
        else:
            details = "<p>No entries for this date.</p>"

        return JsonResponse({'details': details})
    except ValueError as e:
        logger.error(f"Invalid date format: {date}, error: {e}")
        return JsonResponse({'details': '<p>Invalid date format.</p>'}, status=400)
    except Exception as e:
        logger.error(f"Error fetching details for {date}: {e}")
        return JsonResponse({'details': '<p>Failed to load details. Try again later.</p>'}, status=500)
    



@login_required
def generate_report(request):
    user = request.user
    today = date.today()
    start_date = today - relativedelta(days=30)

    # --- Query Data (last 30 days) ---
    bp_data = BPMeasurement.objects.filter(user=user, measurement_date__gte=start_date).order_by('measurement_date')
    weight_data = WeightLog.objects.filter(user=user, log_date__gte=start_date).order_by('log_date')
    diet_data = DietLog.objects.filter(user=user, log_date__gte=start_date).order_by('log_date')
    symptom_data = SymptomLog.objects.filter(user=user, log_date__gte=start_date).order_by('log_date')

    # --- Summaries ---
    bp_summary = bp_data.aggregate(
        avg_systolic=Avg('systolic_bp'),
        avg_diastolic=Avg('diastolic_bp'),
        avg_heart_rate=Avg('heart_rate')
    )
    weight_summary = weight_data.aggregate(avg_weight=Avg('weight'))
    diet_summary = diet_data.aggregate(
        avg_sodium=Avg('sodium_intake'),
        avg_potassium=Avg('potassium_intake'),
        avg_carb=Avg('carb_intake')
    )
    symptom_summary = symptom_data.values('severity').annotate(count=Count('id'))

    # --- Generate Graphs ---
    bp_graph = generate_line_graph(bp_data, 'measurement_date', ['systolic_bp', 'diastolic_bp'], 'BP Trends', 'Date', 'BP (mmHg)')
    weight_graph = generate_line_graph(weight_data, 'log_date', ['weight'], 'Weight Trends', 'Date', 'Weight (kg)')
    diet_graph = generate_line_graph(diet_data, 'log_date', ['sodium_intake', 'potassium_intake', 'carb_intake'], 'Diet Trends', 'Date', 'Intake')
    symptom_graph = generate_bar_graph(symptom_data, 'severity', 'Symptom Severity Count', 'Severity', 'Count')
    # --- User Profile Info ---
    try:
        profile = user.userprofile
        dob = profile.date_of_birth
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day)) if dob else "N/A"
        gender = profile.gender or "N/A"
    except UserProfile.DoesNotExist:
        age, gender = "N/A", "N/A"

    current_weight = weight_data.last().weight if weight_data.exists() else profile.initial_weight if 'profile' in locals() else "N/A"

    context = {
        "name": user.first_name or user.username,
        "age": age,
        "gender": gender,
        "current_weight": current_weight,

        "bp_data": bp_data,
        "weight_data": weight_data,
        "diet_data": diet_data,
        "symptom_data": symptom_data,

        "bp_summary": bp_summary,
        "weight_summary": weight_summary,
        "diet_summary": diet_summary,
        "symptom_summary": symptom_summary,

        "bp_graph": bp_graph,
        "weight_graph": weight_graph,
        "diet_graph": diet_graph,
        "symptom_graph": symptom_graph,
    }
    return render(request, "app/report.html", context)

@login_required
def download_report(request):
    # Fetch user profile
    profile = UserProfile.objects.get(user=request.user)
    name = request.user.get_full_name() or request.user.username
    age = (date.today() - profile.date_of_birth).days // 365 if hasattr(profile, 'date_of_birth') else 'N/A'
    gender = profile.gender if hasattr(profile, 'gender') else 'N/A'
    current_weight = profile.initial_weight
    latest_weight = WeightLog.objects.filter(user=request.user).order_by('-log_date').first()
    if latest_weight:
        current_weight = latest_weight.weight

    # Fetch data for last 30 days
    start_date = date.today() - relativedelta(months=1)
    bp_data = BPMeasurement.objects.filter(user=request.user, measurement_date__gte=start_date).order_by('measurement_date')
    weight_data = WeightLog.objects.filter(user=request.user, log_date__gte=start_date).order_by('log_date')
    diet_data = DietLog.objects.filter(user=request.user, log_date__gte=start_date).order_by('log_date')
    symptom_data = SymptomLog.objects.filter(user=request.user, log_date__gte=start_date).order_by('log_date')

    # Summaries
    bp_summary = bp_data.aggregate(avg_systolic=Avg('systolic_bp'), avg_diastolic=Avg('diastolic_bp'), avg_heart_rate=Avg('heart_rate'))
    weight_summary = weight_data.aggregate(avg_weight=Avg('weight'))
    diet_summary = diet_data.aggregate(avg_sodium=Avg('sodium_intake'), avg_potassium=Avg('potassium_intake'), avg_carb=Avg('carb_intake'))
    symptom_summary = symptom_data.values('severity').annotate(count=Count('severity'))

    # Generate graphs
    bp_graph = generate_line_graph(bp_data, 'measurement_date', ['systolic_bp', 'diastolic_bp'], 'BP Trends', 'Date', 'BP (mmHg)')
    weight_graph = generate_line_graph(weight_data, 'log_date', ['weight'], 'Weight Trends', 'Date', 'Weight (kg)')
    diet_graph = generate_line_graph(diet_data, 'log_date', ['sodium_intake', 'potassium_intake', 'carb_intake'], 'Diet Trends', 'Date', 'Intake (mg/g)')
    symptom_graph = generate_bar_graph(symptom_data, 'severity', 'Symptoms Severity Count', 'Severity', 'Count')

    # Create PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{name}_Health_Report_{date.today().strftime("%Y%m%d")}.pdf"'

    # PDF document setup
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name='Title', parent=styles['Heading1'], fontSize=18, textColor=colors.darkblue)
    header_style = ParagraphStyle(name='Header', parent=styles['Heading2'], fontSize=14, textColor=colors.black)
    normal_style = styles['Normal']

    # Patient Information
    elements.append(Paragraph(f"Health Report for {name}", title_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Age: {age} | Gender: {gender} | Current Weight: {current_weight} kg", normal_style))
    elements.append(Spacer(1, 24))

    # BP Section
    elements.append(Paragraph("BP Measurements", header_style))
    if bp_data.exists():
        data = [['Date', 'Systolic BP', 'Diastolic BP', 'Heart Rate', 'Notes']]
        for entry in bp_data:
            data.append([
                entry.measurement_date.strftime('%Y-%m-%d'),
                str(entry.systolic_bp),
                str(entry.diastolic_bp),
                str(entry.heart_rate or ''),
                entry.notes or ''
            ])
        table = Table(data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(table)
        elements.append(Paragraph(f"Average: {bp_summary['avg_systolic'] or 'N/A'} / {bp_summary['avg_diastolic'] or 'N/A'} mmHg, Avg HR: {bp_summary['avg_heart_rate'] or 'N/A'} bpm", normal_style))
    else:
        elements.append(Paragraph("No BP data available.", normal_style))
    elements.append(Spacer(1, 24))

    # Weight Section
    elements.append(Paragraph("Weight Logs", header_style))
    if weight_data.exists():
        data = [['Date', 'Weight (kg)']]
        for entry in weight_data:
            data.append([entry.log_date.strftime('%Y-%m-%d'), str(entry.weight)])
        table = Table(data, colWidths=[1.5*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(table)
        elements.append(Paragraph(f"Average Weight: {weight_summary['avg_weight'] or 'N/A'} kg", normal_style))
    else:
        elements.append(Paragraph("No weight data available.", normal_style))
    elements.append(Spacer(1, 24))

    # Diet Section
    elements.append(Paragraph("Diet Logs", header_style))
    if diet_data.exists():
        data = [['Date', 'Sodium (mg)', 'Potassium (mg)', 'Carbs (g)']]
        for entry in diet_data:
            data.append([entry.log_date.strftime('%Y-%m-%d'), str(entry.sodium_intake), str(entry.potassium_intake), str(entry.carb_intake)])
        table = Table(data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(table)
        elements.append(Paragraph(f"Average Sodium: {diet_summary['avg_sodium'] or 'N/A'} mg, Potassium: {diet_summary['avg_potassium'] or 'N/A'} mg, Carbs: {diet_summary['avg_carb'] or 'N/A'} g", normal_style))
    else:
        elements.append(Paragraph("No diet data available.", normal_style))
    elements.append(Spacer(1, 24))

    # Symptom Section
    elements.append(Paragraph("Symptoms", header_style))
    if symptom_data.exists():
        data = [['Date', 'Description', 'Severity']]
        for entry in symptom_data:
            data.append([entry.log_date.strftime('%Y-%m-%d'), entry.symptom_description, entry.severity])
        table = Table(data, colWidths=[1.5*inch, 2*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(table)
        elements.append(Paragraph("Symptom Summary:", normal_style))
        for item in symptom_summary:
            elements.append(Paragraph(f"{item['severity']}: {item['count']}", normal_style))
    else:
        elements.append(Paragraph("No symptom data available.", normal_style))
    elements.append(Spacer(1, 24))

    # Add Graphs
    if bp_graph:
        elements.append(Paragraph("BP Trends", header_style))
        img = Image(io.BytesIO(base64.b64decode(bp_graph)), width=4*inch, height=3*inch)
        elements.append(img)
        elements.append(Spacer(1, 12))
    if weight_graph:
        elements.append(Paragraph("Weight Trends", header_style))
        img = Image(io.BytesIO(base64.b64decode(weight_graph)), width=4*inch, height=3*inch)
        elements.append(img)
        elements.append(Spacer(1, 12))
    if diet_graph:
        elements.append(Paragraph("Diet Trends", header_style))
        img = Image(io.BytesIO(base64.b64decode(diet_graph)), width=4*inch, height=3*inch)
        elements.append(img)
        elements.append(Spacer(1, 12))
    if symptom_graph:
        elements.append(Paragraph("Symptoms Severity Count", header_style))
        img = Image(io.BytesIO(base64.b64decode(symptom_graph)), width=4*inch, height=3*inch)
        elements.append(img)
        elements.append(Spacer(1, 12))

    # Build PDF
    doc.build(elements)
    return response


def generate_line_graph(data, date_field, value_fields, title, xlabel, ylabel):
    if not data.exists():
        return None
    dates = [getattr(entry, date_field) for entry in data]
    values = {field: [getattr(entry, field) for entry in data] for field in value_fields}

    fig, ax = plt.subplots()
    for field in value_fields:
        ax.plot(dates, values[field], label=field.replace('_', ' ').title(), marker='o')
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()
    ax.grid(True)
    ax.tick_params(axis='x', rotation=45)
    fig.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    return img_base64

def generate_bar_graph(data, category_field, title, xlabel, ylabel):
    if not data.exists():
        return None
    categories = list(set([getattr(entry, category_field) for entry in data]))
    counts = [data.filter(**{category_field: cat}).count() for cat in categories]

    fig, ax = plt.subplots()
    ax.bar(categories, counts, color='skyblue')
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis='y')

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    return img_base64


