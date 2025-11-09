"""
Integration tests for views with database and services.
"""
import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.integration
@pytest.mark.django_db
class TestViewsIntegration:
    """Test complete view workflows with database"""

    def test_complete_search_workflow(self, test_user_with_profile, multiple_cases):
        """Test complete search workflow from login to results"""
        client = Client()
        client.force_login(test_user_with_profile)

        # Navigate to advanced search
        response = client.get(reverse('legal_research:search'))
        assert response.status_code == 200

        # Submit search
        response = client.post(
            reverse('legal_research:search_results'),
            {'query': 'contract law'}
        )
        assert response.status_code == 200

        # Verify SearchHistory was created
        from legal_research.models import SearchHistory
        assert SearchHistory.objects.filter(user=test_user_with_profile).exists()


@pytest.mark.integration
@pytest.mark.django_db
class TestCaseWorkflow:
    """Test case viewing and interaction workflow"""

    def test_view_save_and_note_case(self, test_user, test_case):
        """Test viewing, saving, and adding note to a case"""
        client = Client()
        client.force_login(test_user)

        # View case
        response = client.get(
            reverse('legal_research:case_detail', kwargs={'case_id': test_case.id})
        )
        assert response.status_code == 200

        # Save case
        response = client.get(
            reverse('legal_research:save_case', kwargs={'case_id': test_case.id})
        )
        assert response.status_code == 302

        # Verify case was saved
        from legal_research.models import SavedCase
        assert SavedCase.objects.filter(user=test_user, case=test_case).exists()

        # Add note
        response = client.post(
            reverse('legal_research:save_case_note', kwargs={'case_id': test_case.id}),
            {'note_text': 'Important case'}
        )
        assert response.status_code == 200

        # Verify note was created
        from legal_research.models import UserNote
        assert UserNote.objects.filter(user=test_user, case=test_case).exists()
