from django.urls import path
from .views import (
    ReviewWorkspaceView, ReviewHistoryView, ReviewDetailView, 
    DownloadPDFView, ExportCSVView, DeleteReviewView, ReviewChatView
)

urlpatterns = [
    path('', ReviewWorkspaceView.as_view(), name='review'),
    path('history/', ReviewHistoryView.as_view(), name='review_history'),
    path('detail/<int:pk>/', ReviewDetailView.as_view(), name='review_detail'),
    path('detail/<int:pk>/chat/', ReviewChatView.as_view(), name='review_chat'),
    path('pdf/<int:pk>/', DownloadPDFView.as_view(), name='download_pdf'),
    path('csv/', ExportCSVView.as_view(), name='export_csv'),
    path('delete/<int:pk>/', DeleteReviewView.as_view(), name='delete_review'),
]
