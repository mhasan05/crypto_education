from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class UserAuthAdmin(UserAdmin):
    model = User
    list_display = ('email', 'full_name', 'role', 'subscription', 'is_active', 'is_staff')
    ordering = ('email',)
    search_fields = ('email', 'full_name')
    list_filter = ('is_staff', 'is_active', 'role', 'subscription')

    fieldsets = (
    ('Login credential', {'fields': ('email', 'google_id', 'password')}),
    ('Personal Info', {'fields': ('full_name', 'image','google_image_url', 'role', 'language', 'subscription', 'videos_progress')}),
    ('verification', {'fields': ('otp', 'otp_expired')}),
    ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    ('Important dates', {'fields': ('date_joined',)}), 
)


    readonly_fields = ('last_login', 'date_joined')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

admin.site.register(User, UserAuthAdmin)
