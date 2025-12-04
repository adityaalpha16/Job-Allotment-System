# JobManage Pro - Job Management Portal

## Overview
A comprehensive job management portal built with Django and Bootstrap 5. Features role-based access control with three user types (Admin, Supervisor, Employee), Kanban-style job board, team management, and dark/light theme support.

## Tech Stack
- **Backend**: Django 5.x
- **Frontend**: HTML5, Bootstrap 5, Bootstrap Icons
- **Database**: SQLite (development)
- **Charts**: Chart.js
- **Excel Processing**: openpyxl

## User Roles & Permissions

### Admin
- Full access to Dashboard, Job Board, Team Management, Previous Contributors
- Can view ALL users
- Can Create, Edit (Name, Phone, Role), and Soft Delete users
- Cannot edit Salary or Rating
- Can view and restore deleted users (Previous Contributors)
- Can create, edit, delete, and verify any job

### Supervisor
- Access to Dashboard, Job Board, Team Management
- Can ONLY see Employees (not Admins or other Supervisors)
- Can ONLY edit Salary and Rating (1-5 Stars)
- Can create jobs, assign to employees, and verify completion

### Employee
- Access to Dashboard, My Jobs
- No access to Team Management
- Can only view jobs assigned to them
- Can change status: PENDING -> IN_PROGRESS -> SUBMITTED
- Cannot verify jobs

## Job Statuses
1. **PENDING** - Job created, not started
2. **IN_PROGRESS** - Work in progress
3. **SUBMITTED** - Submitted for review
4. **VERIFIED** - Completed and verified

## Seed Data Credentials
- Admin: `admin` / `admin123`
- Supervisor: `supervisor` / `supervisor123`
- Employee: `employee1` / `employee123`
- Employee: `employee2` / `employee123`

## Project Structure
```
├── core/                   # Main Django app
│   ├── models.py          # User and Job models
│   ├── views.py           # All view functions
│   ├── urls.py            # URL routing
│   ├── admin.py           # Django admin config
│   └── management/
│       └── commands/
│           └── seed_data.py  # Database seeding
├── templates/             # HTML templates
│   ├── base.html          # Base layout with sidebar
│   ├── login.html         # Login page
│   ├── signup.html        # Signup with role selection
│   ├── dashboard.html     # Dashboard with charts
│   ├── job_board.html     # Kanban job board
│   ├── my_jobs.html       # Employee job view
│   ├── job_form.html      # Job create/edit form
│   ├── team_management.html  # Team list
│   ├── team_form.html     # User create/edit form
│   └── previous_contributors.html  # Deleted users
├── static/                # Static files
├── jobmanage/             # Django project settings
└── manage.py
```

## Features
- Dark/Light theme toggle
- Responsive sidebar navigation
- Chart.js dashboard visualizations
- Kanban-style job board
- Excel (.xlsx) import for bulk user creation
- Soft delete with restore functionality
- Role-based visibility and permissions
- 5-star rating system for employees

## Running the Project
```bash
python manage.py runserver 0.0.0.0:5000
```

## Management Commands
```bash
python manage.py seed_data  # Seed database with sample data
python manage.py migrate    # Apply migrations
```
