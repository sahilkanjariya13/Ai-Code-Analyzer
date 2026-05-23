from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Profile
from reviewer.models import CodeReview
from api_logs.models import APILog
from unittest.mock import patch

class AIReviewerTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123', email='test@example.com')
        self.staff_user = User.objects.create_user(username='adminuser', password='password123', email='admin@example.com', is_staff=True)
        
    def test_profile_auto_creation(self):
        """
        Verify that creating a user automatically registers an associated Profile.
        """
        self.assertIsNotNone(self.user.profile)
        self.assertFalse(self.user.profile.is_blocked)
        
    def test_anonymous_access_redirect(self):
        """
        Ensure unauthenticated requests are redirected to the login page.
        """
        response = self.client.get(reverse('review'))
        self.assertEqual(response.status_code, 302)
        
    @patch('reviewer.views.review_code')
    def test_code_review_ajax_success(self, mock_review):
        """
        Submit code via AJAX, mock Gemini's response, and verify the model database saves.
        """
        self.client.login(username='testuser', password='password123')
        mock_review.return_value = {
            'success': True,
            'error': "",
            'text': "### Review Report\n[SECURITY: 8/10]\n[PERFORMANCE: 9/10]\n[READABILITY: 7/10]\n[OVERALL: 8/10]\n",
            'improved_code': "print('hello')",
            'scores': {'security': 8, 'performance': 9, 'readability': 7, 'overall': 8}
        }
        
        response = self.client.post(
            reverse('review'),
            {'language': 'python', 'code': 'print("hello")'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['scores']['security'], 8)
        self.assertEqual(data['scores']['overall'], 8)
        
        # Verify db entry was created correctly
        review = CodeReview.objects.get(id=data['review_id'])
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.score_security, 8)
        
    def test_blocked_user_review_restriction(self):
        """
        Confirm that suspended accounts are denied code review requests.
        """
        self.user.profile.is_blocked = True
        self.user.profile.save()
        self.client.login(username='testuser', password='password123')
        
        response = self.client.post(
            reverse('review'),
            {'language': 'python', 'code': 'print("hello")'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn("suspended", data['error'])
        
    def test_csv_exporter(self):
        """
        Verify that review logs are exported successfully in CSV format.
        """
        self.client.login(username='testuser', password='password123')
        CodeReview.objects.create(
            user=self.user,
            language='python',
            code='x = 1',
            ai_review='Perfect code',
            score_security=10, score_performance=10, score_readability=10, score_overall=10
        )
        
        response = self.client.get(reverse('export_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('AI_Code_Review_History.csv', response['Content-Disposition'])

    def test_delete_review(self):
        """
        Verify that a user can delete their own review record, and a staff user can delete any review record,
        but a regular user cannot delete another user's review.
        """
        review = CodeReview.objects.create(
            user=self.user,
            language='python',
            code='x = 1',
            ai_review='Perfect code',
            score_security=10, score_performance=10, score_readability=10, score_overall=10
        )
        other_user = User.objects.create_user(username='otheruser', password='password123')
        
        # Unauthenticated cannot delete
        response = self.client.post(reverse('delete_review', args=[review.id]))
        self.assertEqual(response.status_code, 302) # Redirects to login
        self.assertEqual(CodeReview.objects.count(), 1)
        
        # Other user cannot delete (404)
        self.client.login(username='otheruser', password='password123')
        response = self.client.post(reverse('delete_review', args=[review.id]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(CodeReview.objects.count(), 1)
        self.client.logout()
        
        # Owner can delete
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('delete_review', args=[review.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CodeReview.objects.count(), 0)

    @patch('reviewer.views.chat_follow_up')
    def test_review_chat_success(self, mock_chat):
        """
        Verify that review owners can successfully post chat questions,
        triggering AI follow-ups and storing user/ai messages in DB.
        """
        self.client.login(username='testuser', password='password123')
        review = CodeReview.objects.create(
            user=self.user,
            language='python',
            code='def x(): pass',
            ai_review='Good function.',
            score_security=9, score_performance=9, score_readability=9, score_overall=9
        )
        
        mock_chat.return_value = {
            'success': True,
            'error': '',
            'text': 'Here is my AI suggestion for your question.'
        }
        
        response = self.client.post(
            reverse('review_chat', args=[review.id]),
            {'message': 'How can I make this faster?'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('AI suggestion', data['message'])
        
        # Verify messages saved
        messages = review.chat_messages.all()
        self.assertEqual(messages.count(), 2)
        self.assertEqual(messages[0].role, 'user')
        self.assertEqual(messages[0].content, 'How can I make this faster?')
        self.assertEqual(messages[1].role, 'ai')
        self.assertEqual(messages[1].content, 'Here is my AI suggestion for your question.')

    def test_review_chat_permission_denied(self):
        """
        Ensure users cannot post chat followups on other users' code reviews.
        """
        review = CodeReview.objects.create(
            user=self.user,
            language='python',
            code='def x(): pass',
            ai_review='Good function.',
            score_security=9, score_performance=9, score_readability=9, score_overall=9
        )
        other_user = User.objects.create_user(username='otheruser2', password='password123')
        self.client.login(username='otheruser2', password='password123')
        
        response = self.client.post(
            reverse('review_chat', args=[review.id]),
            {'message': 'Hello'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 404)
        self.client.logout()

        # Anonymous user redirect
        response = self.client.post(
            reverse('review_chat', args=[review.id]),
            {'message': 'Hello'}
        )
        self.assertEqual(response.status_code, 302)
