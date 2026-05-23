from django.urls import path
from .views import dashboard_view, toggle_user_block

urlpatterns = [
    path('', dashboard_view, name='dashboard'),
    path('block/<int:user_id>/', toggle_user_block, name='toggle_user_block'),
]
