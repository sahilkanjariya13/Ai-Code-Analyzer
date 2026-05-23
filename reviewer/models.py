from django.db import models
from django.contrib.auth.models import User

class CodeReview(models.Model):
    LANGUAGE_CHOICES = (
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        ('csharp', 'C#'),
        ('go', 'Go'),
        ('rust', 'Rust'),
        ('php', 'PHP'),
        ('html', 'HTML'),
        ('css', 'CSS'),
        ('sql', 'SQL'),
        ('django', 'Django'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    language = models.CharField(max_length=100, choices=LANGUAGE_CHOICES)
    code = models.TextField()
    ai_review = models.TextField(blank=True, null=True)
    improved_code = models.TextField(blank=True, null=True, help_text="AI suggested corrected code version")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Detailed criteria scores parsed from response
    score_security = models.IntegerField(default=0, help_text="Security Score out of 10")
    score_performance = models.IntegerField(default=0, help_text="Performance Score out of 10")
    score_readability = models.IntegerField(default=0, help_text="Readability Score out of 10")
    score_overall = models.IntegerField(default=0, help_text="Overall Score out of 10")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_language_display()} ({self.score_overall}/10)"


class ChatMessage(models.Model):
    review = models.ForeignKey(CodeReview, on_delete=models.CASCADE, related_name='chat_messages')
    role = models.CharField(max_length=20, choices=(('user', 'User'), ('ai', 'AI')))
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.review.user.username} - {self.role.upper()} message ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
