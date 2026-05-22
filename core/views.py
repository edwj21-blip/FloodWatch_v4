from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import WaterLevel, FloodAlert, FloodReport, RescueTeam, EmergencyContact
from .forms import FloodReportForm, LoginForm


# ─── Portal / Landing Page ────────────────────────────────────────────────────

def portal_view(request):
    """Public landing page — choose user or admin portal."""
    if request.user.is_authenticated:
        return redirect('admin_reports' if request.user.is_staff else 'home')
    stats = {
        'active_alerts': FloodAlert.objects.filter(is_active=True).count(),
        'critical_zones': WaterLevel.objects.filter(status__in=['DANGER', 'CRITICAL']).count(),
        'reports_today': FloodReport.objects.filter(reported_at__date=timezone.now().date()).count(),
        'rescue_teams': RescueTeam.objects.filter(is_available=True).count(),
    }
    return render(request, 'core/portal.html', stats)


# ─── Dashboard (Home) ─────────────────────────────────────────────────────────

@login_required
def home(request):
    alerts = FloodAlert.objects.filter(is_active=True).order_by('-issued_at')[:5]
    water_levels = WaterLevel.objects.all().order_by('-last_updated')[:8]
    recent_reports = FloodReport.objects.filter(status__in=['PENDING', 'VERIFIED']).order_by('-reported_at')[:6]
    rescue_teams = RescueTeam.objects.filter(is_available=True)[:6]

    stats = {
        'active_alerts': FloodAlert.objects.filter(is_active=True).count(),
        'critical_zones': WaterLevel.objects.filter(status__in=['DANGER', 'CRITICAL']).count(),
        'reports_today': FloodReport.objects.filter(reported_at__date=timezone.now().date()).count(),
        'rescue_teams': RescueTeam.objects.filter(is_available=True).count(),
    }

    context = {
        'alerts': alerts,
        'water_levels': water_levels,
        'recent_reports': recent_reports,
        'rescue_teams': rescue_teams,
        'stats': stats,
        'page': 'home',
    }
    return render(request, 'core/home.html', context)


# ─── Alerts ──────────────────────────────────────────────────────────────────

@login_required
def alerts_view(request):
    severity = request.GET.get('severity', '')
    district = request.GET.get('district', '')
    alerts = FloodAlert.objects.all()
    if severity:
        alerts = alerts.filter(severity=severity)
    if district:
        alerts = alerts.filter(district__icontains=district)
    districts = FloodAlert.objects.values_list('district', flat=True).distinct()
    return render(request, 'core/alerts.html', {
        'alerts': alerts, 'districts': districts,
        'selected_severity': severity, 'selected_district': district, 'page': 'alerts'
    })


# ─── Water Levels ────────────────────────────────────────────────────────────

@login_required
def water_levels_view(request):
    levels = WaterLevel.objects.all().order_by('district', 'location_name')
    status_filter = request.GET.get('status', '')
    if status_filter:
        levels = levels.filter(status=status_filter)
    return render(request, 'core/water_levels.html', {
        'levels': levels, 'status_filter': status_filter, 'page': 'water_levels'
    })


# ─── Report Flood ─────────────────────────────────────────────────────────────

@login_required
def report_flood(request):
    if request.method == 'POST':
        form = FloodReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save()
            messages.success(request, f'✅ Flood report submitted! Report ID: #{report.id}.')
            return redirect('report_success', pk=report.pk)
        else:
            messages.error(request, 'Please fix the errors below and resubmit.')
    else:
        form = FloodReportForm()
    return render(request, 'core/report_flood.html', {'form': form, 'page': 'report'})


def report_success(request, pk):
    report = get_object_or_404(FloodReport, pk=pk)
    return render(request, 'core/report_success.html', {'report': report})


# ─── Rescue Teams ─────────────────────────────────────────────────────────────

@login_required
def rescue_teams_view(request):
    district = request.GET.get('district', '')
    team_type = request.GET.get('type', '')
    teams = RescueTeam.objects.all()
    if district:
        teams = teams.filter(district__icontains=district)
    if team_type:
        teams = teams.filter(team_type=team_type)
    emergency_contacts = EmergencyContact.objects.filter(is_active=True)
    districts = RescueTeam.objects.values_list('district', flat=True).distinct()
    return render(request, 'core/rescue_teams.html', {
        'teams': teams,
        'emergency_contacts': emergency_contacts,
        'districts': districts,
        'selected_district': district,
        'selected_type': team_type,
        'team_types': RescueTeam._meta.get_field('team_type').choices,
        'page': 'rescue',
    })


# ─── Control Rooms ────────────────────────────────────────────────────────────

@login_required
def control_rooms_view(request):
    return render(request, 'core/control_rooms.html', {'page': 'control_rooms'})


# ─── My Reports ──────────────────────────────────────────────────────────────

@login_required
def my_reports(request):
    phone = request.GET.get('phone', '')
    reports = []
    if phone:
        reports = FloodReport.objects.filter(reporter_phone=phone).order_by('-reported_at')
    return render(request, 'core/my_reports.html', {'reports': reports, 'phone': phone, 'page': 'my_reports'})


# ─── Admin Reports ────────────────────────────────────────────────────────────

def admin_reports_view(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, 'You need admin access to view this page.')
        return redirect('login')

    filter_status = request.GET.get('status', '')
    filter_district = request.GET.get('district', '')
    filter_severity = request.GET.get('severity', '')
    filter_evacuation = request.GET.get('evacuation', '')

    reports = FloodReport.objects.all().select_related('rescue_team_assigned', 'reviewed_by')
    if filter_status:
        reports = reports.filter(status=filter_status)
    if filter_district:
        reports = reports.filter(district=filter_district)
    if filter_severity:
        reports = reports.filter(severity=filter_severity)
    if filter_evacuation == 'yes':
        reports = reports.filter(evacuation_needed=True)
    reports = reports.order_by('-reported_at')

    stats = {
        'pending': FloodReport.objects.filter(status='PENDING').count(),
        'verified': FloodReport.objects.filter(status='VERIFIED').count(),
        'resolved': FloodReport.objects.filter(status='RESOLVED').count(),
        'rejected': FloodReport.objects.filter(status='REJECTED').count(),
        'evacuation': FloodReport.objects.filter(evacuation_needed=True, status__in=['PENDING', 'VERIFIED']).count(),
        'total': FloodReport.objects.count(),
    }

    districts = FloodReport.objects.values_list('district', flat=True).distinct().order_by('district')
    rescue_teams = RescueTeam.objects.all().order_by('district', 'name')
    water_overview = WaterLevel.objects.all().order_by('-last_updated')[:12]

    return render(request, 'core/admin_reports.html', {
        'reports': reports,
        'stats': stats,
        'districts': districts,
        'rescue_teams': rescue_teams,
        'water_overview': water_overview,
        'filter_status': filter_status,
        'filter_district': filter_district,
        'filter_severity': filter_severity,
        'filter_evacuation': filter_evacuation,
        'page': 'admin_reports',
    })


def admin_report_action(request, pk):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('login')
    report = get_object_or_404(FloodReport, pk=pk)
    if request.method == 'POST':
        quick = request.POST.get('quick_action', '')
        if quick == 'verify':
            report.status = 'VERIFIED'
        elif quick == 'reject':
            report.status = 'REJECTED'
        elif quick == 'resolve':
            report.status = 'RESOLVED'
        else:
            report.status = request.POST.get('status', report.status)

        rescue_team_id = request.POST.get('rescue_team', '')
        if rescue_team_id:
            try:
                report.rescue_team_assigned_id = int(rescue_team_id)
            except (ValueError, TypeError):
                pass
        else:
            report.rescue_team_assigned = None

        report.admin_notes = request.POST.get('admin_notes', '')
        report.reviewed_by = request.user
        report.save()
        messages.success(request, f'✅ Report #{pk} updated to {report.status}.')

    referer = request.META.get('HTTP_REFERER', '/admin-reports/')
    if '/admin-reports/' in referer:
        return redirect(referer)
    return redirect('admin_reports')


# ─── API Endpoints ────────────────────────────────────────────────────────────

def api_water_levels(request):
    """JSON endpoint: live water levels with weather data."""
    levels = WaterLevel.objects.all().values(
        'id', 'location_name', 'district',
        'current_level_meters', 'danger_level_meters', 'warning_level_meters',
        'status', 'last_updated',
        'rainfall_mm', 'temperature_c', 'humidity_pct',
        'weather_description', 'rainfall_accuracy_pct', 'weather_icon',
        'api_last_synced',
    )
    data = []
    for lvl in levels:
        lvl['percentage'] = int((lvl['current_level_meters'] / lvl['danger_level_meters']) * 100) \
            if lvl['danger_level_meters'] else 0
        lvl['last_updated'] = lvl['last_updated'].strftime('%d %b %Y, %I:%M %p') if lvl['last_updated'] else ''
        lvl['api_last_synced'] = lvl['api_last_synced'].strftime('%d %b %Y, %I:%M %p') if lvl['api_last_synced'] else 'Never'
        data.append(lvl)
    return JsonResponse({'levels': data, 'count': len(data), 'timestamp': timezone.now().isoformat()})


def api_weather_status(request):
    """JSON endpoint: summary of current weather conditions for admin."""
    levels = WaterLevel.objects.all()
    summary = {
        'total': levels.count(),
        'critical': levels.filter(status='CRITICAL').count(),
        'danger': levels.filter(status='DANGER').count(),
        'warning': levels.filter(status='WARNING').count(),
        'watch': levels.filter(status='WATCH').count(),
        'normal': levels.filter(status='NORMAL').count(),
        'avg_rainfall_mm': 0,
        'max_rainfall_mm': 0,
        'active_alerts': FloodAlert.objects.filter(is_active=True).count(),
        'timestamp': timezone.now().isoformat(),
    }
    if levels.exists():
        rainfalls = [l.rainfall_mm for l in levels]
        summary['avg_rainfall_mm'] = round(sum(rainfalls) / len(rainfalls), 1)
        summary['max_rainfall_mm'] = round(max(rainfalls), 1)
    return JsonResponse(summary)


# ─── Auth ─────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('admin_reports' if request.user.is_staff else 'home')
    next_url = request.GET.get('next', '')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data['username'],
                                password=form.cleaned_data['password'])
            if user:
                login(request, user)
                if next_url:
                    return redirect(next_url)
                if user.is_staff:
                    messages.success(request, f'👋 Welcome back, Admin {user.username}!')
                    return redirect('admin_reports')
                else:
                    messages.success(request, f'👋 Welcome, {user.username}!')
                    return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form, 'next': next_url})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('portal')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()

        from django.contrib.auth.models import User as AuthUser
        form_data = {'username': username, 'first_name': first_name,
                     'last_name': last_name, 'email': email}

        if not username:
            messages.error(request, 'Username is required.')
            return render(request, 'core/register.html', {'form_data': form_data})
        if len(username) < 3:
            messages.error(request, 'Username must be at least 3 characters.')
            return render(request, 'core/register.html', {'form_data': form_data})
        if AuthUser.objects.filter(username=username).exists():
            messages.error(request, 'That username is already taken.')
            return render(request, 'core/register.html', {'form_data': form_data})
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'core/register.html', {'form_data': form_data})
        if len(password1) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
            return render(request, 'core/register.html', {'form_data': form_data})

        user = AuthUser.objects.create_user(
            username=username, password=password1,
            first_name=first_name, last_name=last_name, email=email,
        )
        login(request, user)
        messages.success(request, f'🎉 Welcome to FloodWatch Kerala, {username}!')
        return redirect('home')

    return render(request, 'core/register.html', {})
