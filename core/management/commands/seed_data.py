from django.core.management.base import BaseCommand
from core.models import CustomUser, Job, UserRole, JobStatus
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Seed the database with initial data'

    def handle(self, *args, **options):
        if CustomUser.objects.exists():
            self.stdout.write(self.style.WARNING('Database already has data. Skipping seed.'))
            return

        admin = CustomUser.objects.create_user(
            username='admin',
            password='admin123',
            full_name='John Admin',
            phone='555-0100',
            role=UserRole.ADMIN,
            salary=80000.00,
            rating=5
        )
        self.stdout.write(self.style.SUCCESS(f'Created Admin: {admin.username}'))

        supervisor = CustomUser.objects.create_user(
            username='supervisor',
            password='supervisor123',
            full_name='Sarah Manager',
            phone='555-0200',
            role=UserRole.SUPERVISOR,
            salary=60000.00,
            rating=5
        )
        self.stdout.write(self.style.SUCCESS(f'Created Supervisor: {supervisor.username}'))

        employee1 = CustomUser.objects.create_user(
            username='employee1',
            password='employee123',
            full_name='Mike Worker',
            phone='555-0301',
            role=UserRole.EMPLOYEE,
            salary=45000.00,
            rating=4
        )
        self.stdout.write(self.style.SUCCESS(f'Created Employee: {employee1.username}'))

        employee2 = CustomUser.objects.create_user(
            username='employee2',
            password='employee123',
            full_name='Emily Staff',
            phone='555-0302',
            role=UserRole.EMPLOYEE,
            salary=48000.00,
            rating=5
        )
        self.stdout.write(self.style.SUCCESS(f'Created Employee: {employee2.username}'))

        deleted_employee = CustomUser.objects.create_user(
            username='former_employee',
            password='former123',
            full_name='Tom Former',
            phone='555-0400',
            role=UserRole.EMPLOYEE,
            salary=42000.00,
            rating=3,
            is_deleted=True
        )
        self.stdout.write(self.style.SUCCESS(f'Created Deleted Employee: {deleted_employee.username}'))

        Job.objects.create(
            title='Website Redesign',
            description='Redesign the company website with modern UI/UX principles.',
            assigned_to=employee1,
            created_by=admin,
            status=JobStatus.PENDING,
            due_date=date.today() + timedelta(days=14)
        )

        Job.objects.create(
            title='Database Optimization',
            description='Optimize database queries for better performance.',
            assigned_to=employee2,
            created_by=supervisor,
            status=JobStatus.IN_PROGRESS,
            due_date=date.today() + timedelta(days=7)
        )

        Job.objects.create(
            title='API Documentation',
            description='Write comprehensive API documentation for developers.',
            assigned_to=employee1,
            created_by=supervisor,
            status=JobStatus.SUBMITTED,
            due_date=date.today() + timedelta(days=3)
        )

        Job.objects.create(
            title='Security Audit',
            description='Perform a complete security audit of the application.',
            assigned_to=employee2,
            created_by=admin,
            status=JobStatus.VERIFIED,
            due_date=date.today() - timedelta(days=2)
        )

        Job.objects.create(
            title='Legacy Code Migration',
            description='Migrate legacy code to new framework.',
            assigned_to=deleted_employee,
            created_by=admin,
            status=JobStatus.PENDING,
            due_date=date.today() + timedelta(days=21)
        )

        self.stdout.write(self.style.SUCCESS('Created sample jobs'))
        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
