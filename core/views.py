from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.db import transaction
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
            messages.error(request, 'Invalid username or password.')
            return render(request, 'login.html')
        
        user = authenticate(request, username=username, password=password)
        if password == 'password123':
            # messages.warning(request, 'You are using the default password. Please change it after logging in.')
            # login(request, user)
            messages.warning(request, 'Please change your password from the profile settings.')
            
        if user is not None:
            if user.is_deleted:
                messages.error(request, 'Account terminated. Please contact administrator.')
                return render(request, 'login.html')
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = generateEmpId()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        role = request.POST.get('role', UserRole.EMPLOYEE)
        
        if not username or not password or not full_name:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'signup.html')
        
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
            return render(request, 'signup.html')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'signup.html')
        
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'signup.html')
        
        if role not in [UserRole.ADMIN, UserRole.SUPERVISOR, UserRole.EMPLOYEE]:
            role = UserRole.EMPLOYEE
        
        salary = 45000.00
        if role == UserRole.SUPERVISOR:
            salary = 60000.00
        elif role == UserRole.ADMIN:
            salary = 80000.00
        
        user = CustomUser.objects.create_user(
            username=generateEmpId(),
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

def generateEmpId():
    last_user = CustomUser.objects.all().order_by('id').last()
    if not last_user:
        return 'EMP001'
    user_id = last_user.id
    new_id = 'EMP' + str(user_id + 1).zfill(3)
    return new_id

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
        messages.error(request, 'Access denied.')
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
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        assigned_to_id = request.POST.get('assigned_to')
        due_date = request.POST.get('due_date')
        
        if not title:
            messages.error(request, 'Job title is required.')
            employees = CustomUser.objects.filter(role=UserRole.EMPLOYEE, is_deleted=False)
            return render(request, 'job_form.html', {'employees': employees, 'action': 'Create'})
        
        assigned_to = None
        if assigned_to_id:
            try:
                assigned_to = CustomUser.objects.get(id=assigned_to_id, role=UserRole.EMPLOYEE, is_deleted=False)
            except CustomUser.DoesNotExist:
                messages.error(request, 'Invalid employee selected.')
                employees = CustomUser.objects.filter(role=UserRole.EMPLOYEE, is_deleted=False)
                return render(request, 'job_form.html', {'employees': employees, 'action': 'Create'})
        
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
    if request.user.role == UserRole.EMPLOYEE:
        messages.error(request, 'You do not have permission to edit jobs.')
        return redirect('my_jobs')
    
    job = get_object_or_404(Job, id=job_id)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        assigned_to_id = request.POST.get('assigned_to')
        due_date = request.POST.get('due_date')
        
        if not title:
            messages.error(request, 'Job title is required.')
            employees = CustomUser.objects.filter(role=UserRole.EMPLOYEE, is_deleted=False)
            return render(request, 'job_form.html', {'job': job, 'employees': employees, 'action': 'Edit'})
        
        job.title = title
        job.description = description
        
        if assigned_to_id:
            try:
                job.assigned_to = CustomUser.objects.get(id=assigned_to_id, role=UserRole.EMPLOYEE, is_deleted=False)
            except CustomUser.DoesNotExist:
                messages.error(request, 'Invalid employee selected.')
                employees = CustomUser.objects.filter(role=UserRole.EMPLOYEE, is_deleted=False)
                return render(request, 'job_form.html', {'job': job, 'employees': employees, 'action': 'Edit'})
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
        
        if new_status not in [JobStatus.PENDING, JobStatus.IN_PROGRESS, JobStatus.SUBMITTED, JobStatus.VERIFIED]:
            messages.error(request, 'Invalid status.')
            return redirect('job_board')
        
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
        username = generateEmpId()
        password = 'password123'
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        role = request.POST.get('role', UserRole.EMPLOYEE)
        
        if not username or not password or not full_name:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'team_form.html', {'action': 'Create', 'can_edit_name': True})
        
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'team_form.html', {'action': 'Create', 'can_edit_name': True})
        
        if role not in [UserRole.ADMIN, UserRole.SUPERVISOR, UserRole.EMPLOYEE]:
            role = UserRole.EMPLOYEE
        
        salary = 45000.00
        if role == UserRole.SUPERVISOR:
            salary = 60000.00
        elif role == UserRole.ADMIN:
            salary = 80000.00
        
        CustomUser.objects.create_user(
            username=generateEmpId(),
            password=password,
            full_name=full_name,
            phone=phone,
            role=role,
            salary=salary,
            rating=5
        )
        
        messages.success(request, 'User created successfully!')
        return redirect('team_management')
    
    return render(request, 'team_form.html', {'action': 'Create', 'can_edit_name': True})


@login_required
def team_edit(request, user_id):
    target_user = get_object_or_404(CustomUser, id=user_id, is_deleted=False)
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
            full_name = request.POST.get('full_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            new_role = request.POST.get('role')
            
            if full_name:
                target_user.full_name = full_name
            target_user.phone = phone
            
            if new_role and new_role in [UserRole.ADMIN, UserRole.SUPERVISOR, UserRole.EMPLOYEE]:
                target_user.role = new_role
        
        if current_user.role == UserRole.SUPERVISOR:
            salary = request.POST.get('salary')
            rating = request.POST.get('rating')
            
            if salary:
                try:
                    salary_val = float(salary)
                    if salary_val >= 0:
                        target_user.salary = salary_val
                except ValueError:
                    pass
            
            if rating:
                try:
                    rating_val = int(rating)
                    if 1 <= rating_val <= 5:
                        target_user.rating = rating_val
                except ValueError:
                    pass
        
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
    
    if target_user.id == request.user.id:
        messages.error(request, 'You cannot delete yourself.')
        return redirect('team_management')
    
    target_user.is_deleted = True
    target_user.save()
    
    messages.success(request, f'{target_user.username} has been removed from the team.')
    return redirect('team_management')


@login_required
def team_restore(request, user_id):
    if request.user.role != UserRole.ADMIN:
        messages.error(request, 'Only admins can restore users.')
        return redirect('team_management')
    
    target_user = get_object_or_404(CustomUser, id=user_id, is_deleted=True)
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
        
        if not excel_file.name.endswith('.xlsx'):
            messages.error(request, 'Please upload an Excel file (.xlsx).')
            return redirect('team_management')
        
        if excel_file.size > 5 * 1024 * 1024:
            messages.error(request, 'File size must be less than 5MB.')
            return redirect('team_management')
        
        try:
            with transaction.atomic():
                wb = openpyxl.load_workbook(excel_file)
                ws = wb.active
                
                created_count = 0
                errors = []
                
                for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                    if len(row) >= 4:
                        username = str(row[0]).strip() if row[0] else None
                        full_name = str(row[1]).strip() if row[1] else ''
                        phone = str(row[2]).strip() if row[2] else ''
                        salary = row[3]
                        
                        if not username:
                            continue
                        
                        if CustomUser.objects.filter(username=username).exists():
                            errors.append(f'Row {row_num}: Username "{username}" already exists.')
                            continue
                        
                        try:
                            salary_val = float(salary) if salary else 45000.00
                            if salary_val < 0:
                                salary_val = 45000.00
                        except (ValueError, TypeError):
                            salary_val = 45000.00
                        
                        CustomUser.objects.create_user(
                            username=generateEmpId(),
                            password='password123',
                            full_name=full_name,
                            phone=phone,
                            salary=salary_val,
                            role=UserRole.EMPLOYEE,
                            rating=5
                        )
                        created_count += 1
                
                if created_count > 0:
                    messages.success(request, f'Successfully imported {created_count} users.')
                if errors:
                    for error in errors[:5]:
                        messages.warning(request, error)
                    if len(errors) > 5:
                        messages.warning(request, f'...and {len(errors) - 5} more issues.')
                        
        except Exception as e:
            messages.error(request, f'Error importing file: {str(e)}')
        
        return redirect('team_management')
    
    return redirect('team_management')
