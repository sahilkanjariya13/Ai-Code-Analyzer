from django.shortcuts import render, redirect
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from .forms import SignUpForm

class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('review')
        return super().dispatch(request, *args, **kwargs)

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def profile_view(request):
    user = request.user
    # Get user reviews
    user_reviews = user.reviews.all()
    reviews_count = user_reviews.count()
    
    # Calculate averages
    averages = user_reviews.aggregate(
        avg_security=Avg('score_security'),
        avg_performance=Avg('score_performance'),
        avg_readability=Avg('score_readability'),
        avg_overall=Avg('score_overall')
    )
    
    # Language distribution
    lang_distribution = user_reviews.values('language').annotate(count=Count('id')).order_by('-count')

    context = {
        'reviews_count': reviews_count,
        'avg_security': round(averages['avg_security'] or 0, 1),
        'avg_performance': round(averages['avg_performance'] or 0, 1),
        'avg_readability': round(averages['avg_readability'] or 0, 1),
        'avg_overall': round(averages['avg_overall'] or 0, 1),
        'lang_distribution': lang_distribution,
        'recent_reviews': user_reviews[:5]
    }
    return render(request, 'accounts/profile.html', context)
