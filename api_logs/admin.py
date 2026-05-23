from django.contrib import admin
from .models import APILog

@admin.register(APILog)
class APILogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'language', 'latency_ms', 'status', 'timestamp')
    list_filter = ('status', 'language', 'timestamp')
    search_fields = ('user__username', 'error_message', 'language')
    
    # Logs are historical records and should be read-only in the admin panel to prevent tampering
    readonly_fields = ('user', 'language', 'latency_ms', 'status', 'error_message', 'prompt_length', 'response_length', 'timestamp')
    
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return True  # Allow admins to clean up logs if needed
