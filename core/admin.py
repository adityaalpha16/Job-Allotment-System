from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Job


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'full_name', 'role', 'salary', 'rating', 'is_deleted')
    list_filter = ('role', 'is_deleted')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('full_name', 'phone', 'role', 'salary', 'rating', 'is_deleted')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('full_name', 'phone', 'role', 'salary', 'rating')}),
    )


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'assigned_to', 'created_by', 'due_date', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description')
