from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Avg, Q
from .models import CustomUser, Job, UserRole, JobStatus
import openpyxl
from datetime import datetime, timedelta


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            user = CustomUser.objects.get(username=username)
            if user.is_deleted:
                messages.error(request, 'Account terminated. Please contact administrator.')
                return render(request, 'login.html')
        except CustomUser.DoesNotExist:
            pass
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone', '')
        role = request.POST.get('role', UserRole.EMPLOYEE)
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'signup.html')
        
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'signup.html')
        
        salary = 45000.00
        if role == UserRole.SUPERVISOR:
            salary = 60000.00
        elif role == UserRole.ADMIN:
            salary = 80000.00
        
        user = CustomUser.objects.create_user(
            username=username,
            password=password,
            full_name=full_name,
            phone=phone,
            role=role,
            salary=salary,
            rating=5
        )
        
        login(request, user)
        messages.success(request, 'Account created successfully!')
        return redirect('dashboard')
    
    return render(request, 'signup.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    user = request.user
    context = {
        'user': user,
    }
    
    if user.role == UserRole.EMPLOYEE:
        jobs = Job.objects.filter(assigned_to=user)
        context['total_jobs'] = jobs.count()
        context['pending_jobs'] = jobs.filter(status=JobStatus.PENDING).count()
        context['in_progress_jobs'] = jobs.filter(status=JobStatus.IN_PROGRESS).count()
        context['submitted_jobs'] = jobs.filter(status=JobStatus.SUBMITTED).count()
        context['verified_jobs'] = jobs.filter(status=JobStatus.VERIFIED).count()
    else:
        jobs = Job.objects.all()
        context['total_jobs'] = jobs.count()
        context['pending_review'] = jobs.filter(status=JobStatus.SUBMITTED).count()
        context['assigned_by_me'] = jobs.filter(created_by=user).count()
        
        completed_jobs = jobs.filter(status=JobStatus.VERIFIED, completed_at__isnull=False)
        if completed_jobs.exists():
            total_hours = 0
            for job in completed_jobs:
                if job.completed_at and job.created_at:
                    diff = job.completed_at - job.created_at
                    total_hours += diff.total_seconds() / 3600
            context['avg_completion_time'] = round(total_hours / completed_jobs.count(), 1)
        else:
            context['avg_completion_time'] = 0
    
    return render(request, 'dashboard.html', context)


@login_required
def dashboard_stats_api(request):
    user = request.user
    
    if user.role == UserRole.EMPLOYEE:
        jobs = Job.objects.filter(assigned_to=user)
    else:
        jobs = Job.objects.all()
    
    stats = {
        'pending': jobs.filter(status=JobStatus.PENDING).count(),
        'in_progress': jobs.filter(status=JobStatus.IN_PROGRESS).count(),
        'submitted': jobs.filter(status=JobStatus.SUBMITTED).count(),
        'verified': jobs.filter(status=JobStatus.VERIFIED).count(),
    }
    
    return JsonResponse(stats)


@login_required
def job_board(request):
    user = request.user
    
    if user.role == UserRole.EMPLOYEE:
        return redirect('my_jobs')
    
    jobs = Job.objects.select_related('assigned_to', 'created_by').all()
    employees = CustomUser.objects.filter(role=UserRole.EMPLOYEE, is_deleted=False)
    
    pending_jobs = jobs.filter(status=JobStatus.PENDING)
    in_progress_jobs = jobs.filter(status=JobStatus.IN_PROGRESS)
    submitted_jobs = jobs.filter(status=JobStatus.SUBMITTED)
    verified_jobs = jobs.filter(status=JobStatus.VERIFIED)
    
    context = {
        'pending_jobs': pending_jobs,
        'in_progress_jobs': in_progress_jobs,
        'submitted_jobs': submitted_jobs,
        'verified_jobs': verified_jobs,
        'employees': employees,
    }
    
    return render(request, 'job_board.html', context)


@login_required
def my_jobs(request):
    jobs = Job.objects.filter(assigned_to=request.user).select_related('created_by')
    
    pending_jobs = jobs.filter(status=JobStatus.PENDING)
    in_progress_jobs = jobs.filter(status=JobStatus.IN_PROGRESS)
    submitted_jobs = jobs.filter(status=JobStatus.SUBMITTED)
    verified_jobs = jobs.filter(status=JobStatus.VERIFIED)
    
    context = {
        'pending_jobs': pending_jobs,
        'in_progress_jobs': in_progress_jobs,
        'submitted_jobs': submitted_jobs,
        'verified_jobs': verified_jobs,
    }
    
    return render(request, 'my_jobs.html', context)


@login_required
def job_create(request):
    if request.user.role == UserRole.EMPLOYEE:
        messages.error(request, 'You do not have permission to create jobs.')
        return redirect('my_jobs')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        assigned_to_id = request.POST.get('assigned_to')
        due_date = request.POST.get('due_date')
        
        assigned_to = None
        if assigned_to_id:
            assigned_to = get_object_or_404(CustomUser, id=assigned_to_id)
        
        job = Job.objects.create(
            title=title,
            description=description,
            assigned_to=assigned_to,
            created_by=request.user,
            due_date=due_date if due_date else None
        )
        
        messages.success(request, 'Job created successfully!')
        return redirect('job_board')
    
    employees = CustomUser.objects.filter(role=UserRole.EMPLOYEE, is_deleted=False)
    return render(request, 'job_form.html', {'employees': employees, 'action': 'Create'})


@login_required
def job_edit(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    if request.user.role == UserRole.EMPLOYEE:
        messages.error(request, 'You do not have permission to edit jobs.')
        return redirect('my_jobs')
    
    if request.method == 'POST':
        job.title = request.POST.get('title')
        job.description = request.POST.get('description', '')
        assigned_to_id = request.POST.get('assigned_to')
        due_date = request.POST.get('due_date')
        
        if assigned_to_id:
            job.assigned_to = get_object_or_404(CustomUser, id=assigned_to_id)
        else:
            job.assigned_to = None
        
        job.due_date = due_date if due_date else None
        job.save()
        
        messages.success(request, 'Job updated successfully!')
        return redirect('job_board')
    
    employees = CustomUser.objects.filter(role=UserRole.EMPLOYEE, is_deleted=False)
    return render(request, 'job_form.html', {'job': job, 'employees': employees, 'action': 'Edit'})


@login_required
def job_delete(request, job_id):
    if request.user.role == UserRole.EMPLOYEE:
        messages.error(request, 'You do not have permission to delete jobs.')
        return redirect('my_jobs')
    
    job = get_object_or_404(Job, id=job_id)
    job.delete()
    messages.success(request, 'Job deleted successfully!')
    return redirect('job_board')


@login_required
def job_update_status(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        
        if request.user.role == UserRole.EMPLOYEE:
            if job.assigned_to != request.user:
                messages.error(request, 'You can only update your own jobs.')
                return redirect('my_jobs')
            
            if new_status == JobStatus.VERIFIED:
                messages.error(request, 'Employees cannot verify jobs.')
                return redirect('my_jobs')
            
            valid_transitions = {
                JobStatus.PENDING: [JobStatus.IN_PROGRESS],
                JobStatus.IN_PROGRESS: [JobStatus.SUBMITTED],
            }
            
            if new_status not in valid_transitions.get(job.status, []):
                messages.error(request, 'Invalid status transition.')
                return redirect('my_jobs')
        
        job.status = new_status
        if new_status == JobStatus.VERIFIED:
            job.completed_at = timezone.now()
        job.save()
        
        messages.success(request, f'Job status updated to {job.get_status_display()}!')
        
        if request.user.role == UserRole.EMPLOYEE:
            return redirect('my_jobs')
        return redirect('job_board')
    
    return redirect('job_board')


@login_required
def team_management(request):
    user = request.user
    
    if user.role == UserRole.EMPLOYEE:
        messages.error(request, 'You do not have access to team management.')
        return redirect('dashboard')
    
    if user.role == UserRole.SUPERVISOR:
        users = CustomUser.objects.filter(role=UserRole.EMPLOYEE, is_deleted=False)
    else:
        users = CustomUser.objects.filter(is_deleted=False)
    
    context = {
        'team_members': users,
        'can_edit_name': user.role == UserRole.ADMIN,
        'can_edit_salary': user.role == UserRole.SUPERVISOR,
    }
    
    return render(request, 'team_management.html', context)


@login_required
def team_create(request):
    if request.user.role != UserRole.ADMIN:
        messages.error(request, 'Only admins can create users.')
        return redirect('team_management')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone', '')
        role = request.POST.get('role', UserRole.EMPLOYEE)
        
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'team_form.html', {'action': 'Create'})
        
        salary = 45000.00
        if role == UserRole.SUPERVISOR:
            salary = 60000.00
        elif role == UserRole.ADMIN:
            salary = 80000.00
        
        CustomUser.objects.create_user(
            username=username,
            password=password,
            full_name=full_name,
            phone=phone,
            role=role,
            salary=salary,
            rating=5
        )
        
        messages.success(request, 'User created successfully!')
        return redirect('team_management')
    
    return render(request, 'team_form.html', {'action': 'Create'})


@login_required
def team_edit(request, user_id):
    target_user = get_object_or_404(CustomUser, id=user_id)
    current_user = request.user
    
    if current_user.role == UserRole.EMPLOYEE:
        messages.error(request, 'You do not have permission to edit users.')
        return redirect('dashboard')
    
    if current_user.role == UserRole.SUPERVISOR:
        if target_user.role != UserRole.EMPLOYEE:
            messages.error(request, 'You can only edit employees.')
            return redirect('team_management')
    
    if request.method == 'POST':
        if current_user.role == UserRole.ADMIN:
            target_user.full_name = request.POST.get('full_name', target_user.full_name)
            target_user.phone = request.POST.get('phone', target_user.phone)
            new_role = request.POST.get('role')
            if new_role:
                target_user.role = new_role
        
        if current_user.role == UserRole.SUPERVISOR:
            salary = request.POST.get('salary')
            rating = request.POST.get('rating')
            if salary:
                target_user.salary = float(salary)
            if rating:
                target_user.rating = int(rating)
        
        target_user.save()
        messages.success(request, 'User updated successfully!')
        return redirect('team_management')
    
    context = {
        'target_user': target_user,
        'action': 'Edit',
        'can_edit_name': current_user.role == UserRole.ADMIN,
        'can_edit_salary': current_user.role == UserRole.SUPERVISOR,
    }
    
    return render(request, 'team_form.html', context)


@login_required
def team_delete(request, user_id):
    if request.user.role != UserRole.ADMIN:
        messages.error(request, 'Only admins can delete users.')
        return redirect('team_management')
    
    target_user = get_object_or_404(CustomUser, id=user_id)
    target_user.is_deleted = True
    target_user.save()
    
    messages.success(request, f'{target_user.username} has been removed from the team.')
    return redirect('team_management')


@login_required
def team_restore(request, user_id):
    if request.user.role != UserRole.ADMIN:
        messages.error(request, 'Only admins can restore users.')
        return redirect('team_management')
    
    target_user = get_object_or_404(CustomUser, id=user_id)
    target_user.is_deleted = False
    target_user.save()
    
    messages.success(request, f'{target_user.username} has been restored.')
    return redirect('previous_contributors')


@login_required
def previous_contributors(request):
    if request.user.role != UserRole.ADMIN:
        messages.error(request, 'Only admins can view previous contributors.')
        return redirect('team_management')
    
    deleted_users = CustomUser.objects.filter(is_deleted=True)
    
    return render(request, 'previous_contributors.html', {'deleted_users': deleted_users})


@login_required
def team_import(request):
    if request.user.role != UserRole.ADMIN:
        messages.error(request, 'Only admins can import users.')
        return redirect('team_management')
    
    if request.method == 'POST':
        if 'file' not in request.FILES:
            messages.error(request, 'No file uploaded.')
            return redirect('team_management')
        
        excel_file = request.FILES['file']
        
        try:
            wb = openpyxl.load_workbook(excel_file)
            ws = wb.active
            
            created_count = 0
            for row in ws.iter_rows(min_row=2, values_only=True):
                if len(row) >= 4:
                    username, full_name, phone, salary = row[0], row[1], row[2], row[3]
                    
                    if username and not CustomUser.objects.filter(username=username).exists():
                        CustomUser.objects.create_user(
                            username=username,
                            password='password123',
                            full_name=full_name or '',
                            phone=str(phone) if phone else '',
                            salary=float(salary) if salary else 45000.00,
                            role=UserRole.EMPLOYEE,
                            rating=5
                        )
                        created_count += 1
            
            messages.success(request, f'Successfully imported {created_count} users.')
        except Exception as e:
            messages.error(request, f'Error importing file: {str(e)}')
        
        return redirect('team_management')
    
    return redirect('team_management')
