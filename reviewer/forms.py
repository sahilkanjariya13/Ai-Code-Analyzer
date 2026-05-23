from django import forms
from .models import CodeReview

class CodeReviewForm(forms.ModelForm):
    class Meta:
        model = CodeReview
        fields = ['language', 'code']
        widgets = {
            'language': forms.Select(attrs={'class': 'form-select select-premium'}),
            # Hidden because we will bind its value to Monaco Editor before submitting
            'code': forms.Textarea(attrs={'id': 'code-textarea', 'style': 'display:none;'}),
        }
