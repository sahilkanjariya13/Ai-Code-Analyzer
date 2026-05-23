import csv
import markdown
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, Http404
from django.views import View
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.template.loader import get_template
from xhtml2pdf import pisa

from .models import CodeReview, ChatMessage
from .forms import CodeReviewForm
from .gemini_service import review_code, chat_follow_up

class ReviewWorkspaceView(LoginRequiredMixin, View):
    """
    Main workspace rendering the Monaco editor and receiving AJAX code review requests.
    """
    def get(self, request):
        form = CodeReviewForm()
        # Fetch last 3 reviews for the sidebar/recent list
        recent_reviews = CodeReview.objects.filter(user=request.user)[:3]
        return render(request, 'reviewer/workspace.html', {
            'form': form,
            'recent_reviews': recent_reviews
        })

    def post(self, request):
        # Check if the user is blocked
        if hasattr(request.user, 'profile') and request.user.profile.is_blocked:
            return JsonResponse({
                'success': False,
                'error': "Your account has been suspended from using the AI Code Reviewer. Please contact support."
            }, status=403)

        form = CodeReviewForm(request.POST)
        if form.is_valid():
            review_obj = form.save(commit=False)
            review_obj.user = request.user
            
            # Submit to Gemini API and track latency
            result = review_code(review_obj.code, review_obj.language, user=request.user)
            
            if not result['success']:
                return JsonResponse({
                    'success': False,
                    'error': result['error']
                })
            
            review_obj.ai_review = result['text']
            review_obj.improved_code = result['improved_code']
            review_obj.score_security = result['scores']['security']
            review_obj.score_performance = result['scores']['performance']
            review_obj.score_readability = result['scores']['readability']
            review_obj.score_overall = result['scores']['overall']
            review_obj.save()
            
            # Render markdown to HTML for AJAX display
            html_content = markdown.markdown(
                review_obj.ai_review,
                extensions=['markdown.extensions.fenced_code', 'markdown.extensions.codehilite', 'markdown.extensions.tables']
            )

            return JsonResponse({
                'success': True,
                'review_id': review_obj.id,
                'html_content': html_content,
                'improved_code': review_obj.improved_code or "",
                'scores': {
                    'security': review_obj.score_security,
                    'performance': review_obj.score_performance,
                    'readability': review_obj.score_readability,
                    'overall': review_obj.score_overall
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': "Invalid code form data submitted. Please check the language selection and code box."
            })

class ReviewHistoryView(LoginRequiredMixin, ListView):
    """
    Lists all reviews created by the logged-in user with filter options.
    """
    model = CodeReview
    template_name = 'reviewer/history.html'
    context_object_name = 'reviews'
    paginate_by = 10

    def get_queryset(self):
        queryset = CodeReview.objects.filter(user=self.request.user)
        lang = self.request.GET.get('language')
        if lang:
            queryset = queryset.filter(language=lang)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(code__icontains=search) | queryset.filter(ai_review__icontains=search)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['languages'] = CodeReview.LANGUAGE_CHOICES
        context['selected_language'] = self.request.GET.get('language', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context

class ReviewDetailView(LoginRequiredMixin, DetailView):
    """
    Displays details of a single code review with code syntax highlighting.
    """
    model = CodeReview
    template_name = 'reviewer/detail.html'
    context_object_name = 'review'

    def get_queryset(self):
        # Restrict to user's reviews, or staff
        if self.request.user.is_staff:
            return CodeReview.objects.all()
        return CodeReview.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Parse markdown to HTML
        context['review_html'] = markdown.markdown(
            self.object.ai_review,
            extensions=['markdown.extensions.fenced_code', 'markdown.extensions.codehilite', 'markdown.extensions.tables']
        )
        # Load and parse chat messages for UI pre-population
        messages = self.object.chat_messages.all()
        parsed_messages = []
        for msg in messages:
            parsed_content = markdown.markdown(
                msg.content,
                extensions=['markdown.extensions.fenced_code', 'markdown.extensions.codehilite', 'markdown.extensions.tables']
            )
            parsed_messages.append({
                'id': msg.id,
                'role': msg.role,
                'content_html': parsed_content,
                'created_at': msg.created_at
            })
        context['chat_messages'] = parsed_messages
        return context

class DownloadPDFView(LoginRequiredMixin, View):
    """
    Compiles code review report into a structured PDF file download.
    """
    def get(self, request, pk):
        if request.user.is_staff:
            review = get_object_or_404(CodeReview, pk=pk)
        else:
            review = get_object_or_404(CodeReview, pk=pk, user=request.user)
            
        # Parse markdown to HTML for standard tags xhtml2pdf handles
        raw_html = markdown.markdown(
            review.ai_review,
            extensions=['markdown.extensions.tables']
        )
        
        template = get_template('reviewer/review_pdf.html')
        context = {
            'review': review,
            'review_html': raw_html,
            'created_at_formatted': review.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        rendered_html = template.render(context)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="AI_Code_Review_Report_{review.id}.pdf"'
        
        # Create PDF from HTML template
        pisa_status = pisa.CreatePDF(rendered_html, dest=response)
        
        if pisa_status.err:
            return HttpResponse("Error rendering PDF report. Please contact system support.", status=500)
            
        return response

class ExportCSVView(LoginRequiredMixin, View):
    """
    Exports user review history to a downloadable CSV spreadsheet.
    """
    def get(self, request):
        if request.user.is_staff:
            reviews = CodeReview.objects.all()
        else:
            reviews = CodeReview.objects.filter(user=request.user)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="AI_Code_Review_History.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Review ID', 'User', 'Language', 'Submitted Code (Snippet)', 
            'Security Score', 'Performance Score', 'Readability Score', 
            'Overall Score', 'Created At'
        ])
        
        for r in reviews:
            # Truncate submitted code to avoid giant rows
            code_snippet = r.code[:150] + '...' if len(r.code) > 150 else r.code
            writer.writerow([
                r.id, r.user.username, r.get_language_display(), code_snippet,
                r.score_security, r.score_performance, r.score_readability,
                r.score_overall, r.created_at.strftime('%Y-%m-%d %H:%M')
            ])
            
        return response

class DeleteReviewView(LoginRequiredMixin, View):
    """
    Deletes a specific code review from the history.
    """
    def post(self, request, pk):
        if request.user.is_staff:
            review = get_object_or_404(CodeReview, pk=pk)
        else:
            review = get_object_or_404(CodeReview, pk=pk, user=request.user)
        
        review.delete()
        return redirect('review_history')


class ReviewChatView(LoginRequiredMixin, View):
    """
    Handles follow-up chat conversations related to a specific code review.
    """
    def post(self, request, pk):
        if request.user.is_staff:
            review = get_object_or_404(CodeReview, pk=pk)
        else:
            review = get_object_or_404(CodeReview, pk=pk, user=request.user)

        user_message = request.POST.get('message', '').strip()
        if not user_message:
            return JsonResponse({'success': False, 'error': 'Message cannot be empty.'}, status=400)

        # Retrieve existing chat history list before adding the new message
        message_history = list(ChatMessage.objects.filter(review=review).order_by('created_at'))

        # Save user's new chat message
        ChatMessage.objects.create(
            review=review,
            role='user',
            content=user_message
        )

        # Call Gemini AI API with context
        result = chat_follow_up(review, message_history, user_message, user=request.user)
        if not result['success']:
            return JsonResponse({'success': False, 'error': result['error']}, status=500)

        ai_response = result['text']

        # Save AI's chat response
        ChatMessage.objects.create(
            review=review,
            role='ai',
            content=ai_response
        )

        # Format markdown response into HTML for visual representation
        ai_html_message = markdown.markdown(
            ai_response,
            extensions=['markdown.extensions.fenced_code', 'markdown.extensions.codehilite', 'markdown.extensions.tables']
        )

        return JsonResponse({
            'success': True,
            'message': ai_html_message
        })
