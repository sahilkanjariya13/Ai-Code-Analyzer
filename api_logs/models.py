from django.db import models
from django.contrib.auth.models import User

class APILog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='api_logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    language = models.CharField(max_length=50)
    latency_ms = models.IntegerField(help_text="API call latency in milliseconds")
    status = models.CharField(max_length=20, choices=(('SUCCESS', 'Success'), ('FAILED', 'Failed')))
    error_message = models.TextField(null=True, blank=True)
    prompt_length = models.IntegerField(help_text="Character length of the prompt sent to Gemini")
    response_length = models.IntegerField(default=0, help_text="Character length of the response returned by Gemini")

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        user_str = self.user.username if self.user else "Anonymous"
        return f"{user_str} - {self.language} - {self.status} ({self.latency_ms}ms)"
