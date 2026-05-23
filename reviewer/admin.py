from django.contrib import admin
from .models import CodeReview, ChatMessage

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'review', 'role', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('content', 'review__user__username')

@admin.register(CodeReview)
class CodeReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'language', 'score_security', 'score_performance', 'score_readability', 'score_overall', 'created_at')
    list_filter = ('language', 'created_at')
    search_fields = ('user__username', 'code', 'ai_review')
    
    fieldsets = (
        ('Submission Info', {
            'fields': ('user', 'language', 'created_at')
        }),
        ('Scores', {
            'fields': ('score_security', 'score_performance', 'score_readability', 'score_overall')
        }),
        ('Content', {
            'fields': ('code', 'ai_review')
        })
    )
    
    readonly_fields = ('created_at',)
