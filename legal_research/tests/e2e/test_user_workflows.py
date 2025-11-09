"""
End-to-end tests for complete user workflows.
"""
import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.e2e
@pytest.mark.django_db
class TestUserSearchWorkflow:
    """Test complete user search workflow"""

    def test_user_search_to_case_detail_workflow(self, test_user_with_profile, test_case):
        """Test user navigating from login to case detail"""
        client = Client()

        # User logs in
        client.force_login(test_user_with_profile)

        # User navigates to dashboard
        response = client.get(reverse('legal_research:dashboard'))
        assert response.status_code == 200

        # User navigates to search
        response = client.get(reverse('legal_research:search'))
        assert response.status_code == 200

        # User performs search
        response = client.post(
            reverse('legal_research:search_results'),
            {'query': 'contract'}
        )
        assert response.status_code == 200

        # User clicks on case detail
        response = client.get(
            reverse('legal_research:case_detail', kwargs={'case_id': test_case.id})
        )
        assert response.status_code == 200


@pytest.mark.e2e
@pytest.mark.django_db
class TestUserProfileWorkflow:
    """Test user profile management workflow"""

    def test_user_profile_setup_and_update(self, test_user, test_high_court):
        """Test user setting up and updating profile"""
        client = Client()
        client.force_login(test_user)

        # User navigates to profile
        response = client.get(reverse('legal_research:profile'))
        assert response.status_code == 200

        # User updates profile
        response = client.post(
            reverse('legal_research:profile'),
            {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john@example.com',
                'designation': 'Judge',
                'employee_id': 'EMP001',
                'default_language': 'en'
            }
        )
        assert response.status_code == 302

        # Verify profile was created
        from legal_research.models import UserProfile
        assert UserProfile.objects.filter(user=test_user).exists()
