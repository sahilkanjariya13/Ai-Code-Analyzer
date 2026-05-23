import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Avg, Count
from django.utils import timezone
from reviewer.models import CodeReview
from api_logs.models import APILog

@login_required
def dashboard_view(request):
    """
    Renders an analytics dashboard. Admins (staff) see system-wide logs, user lists, 
    and general performance. Regular users see their personal coding reviews statistics.
    """
    is_staff = request.user.is_staff
    
    if is_staff:
        total_users = User.objects.count()
        reviews = CodeReview.objects.all()
        logs = APILog.objects.all()
        user_list = User.objects.select_related('profile').exclude(id=request.user.id)
    else:
        total_users = 1
        reviews = CodeReview.objects.filter(user=request.user)
        logs = APILog.objects.filter(user=request.user)
        user_list = None

    total_reviews = reviews.count()
    
    # Aggregate average code review scores
    averages = reviews.aggregate(
        sec=Avg('score_security'),
        perf=Avg('score_performance'),
        read=Avg('score_readability'),
        over=Avg('score_overall')
    )
    
    # System response and API health statistics
    latency_avg = logs.aggregate(avg=Avg('latency_ms'))['avg'] or 0
    success_count = logs.filter(status='SUCCESS').count()
    failed_count = logs.filter(status='FAILED').count()
    
    total_calls = success_count + failed_count
    success_rate = (success_count / total_calls * 100) if total_calls > 0 else 100
    
    # Calculate language frequency
    lang_stats = reviews.values('language').annotate(count=Count('id')).order_by('-count')
    most_used_lang = lang_stats[0]['language'].upper() if lang_stats else "NONE"
    
    # Datasets for Chart.js graphs
    lang_labels = [l['language'].capitalize() for l in lang_stats]
    lang_counts = [l['count'] for l in lang_stats]
    
    # Calculate reviews per day for the last 7 days
    today = timezone.localdate()
    days = [today - datetime.timedelta(days=i) for i in range(6, -1, -1)]
    day_labels = [d.strftime('%a %d') for d in days]
    day_counts = []
    
    for d in days:
        cnt = reviews.filter(created_at__date=d).count()
        day_counts.append(cnt)

    context = {
        'is_staff': is_staff,
        'total_users': total_users,
        'total_reviews': total_reviews,
        'avg_security': round(averages['sec'] or 0, 1),
        'avg_performance': round(averages['perf'] or 0, 1),
        'avg_readability': round(averages['read'] or 0, 1),
        'avg_overall': round(averages['over'] or 0, 1),
        'latency_avg': round(latency_avg, 1),
        'success_rate': round(success_rate, 1),
        'most_used_lang': most_used_lang,
        'lang_labels': lang_labels,
        'lang_counts': lang_counts,
        'day_labels': day_labels,
        'day_counts': day_counts,
        'user_list': user_list,
        'recent_logs': logs[:10] if is_staff else None
    }
    
    return render(request, 'dashboard/analytics.html', context)

@user_passes_test(lambda u: u.is_staff)
def toggle_user_block(request, user_id):
    """
    Suspends or reactivates a user profile. Only accessible by staff/admin.
    """
    target_user = get_object_or_404(User, id=user_id)
    profile = target_user.profile
    profile.is_blocked = not profile.is_blocked
    profile.save()
    return redirect('dashboard')
