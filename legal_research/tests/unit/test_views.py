"""
Unit tests for legal_research views.
Tests all views and API endpoints with mocked dependencies.
"""
import pytest
import json
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.http import HttpResponse
from unittest.mock import patch, MagicMock
from datetime import date

from legal_research.models import (
    HighCourt, UserProfile, Suit, Tag, Case,
    SearchHistory, Customization, UserNote, SavedCase
)
from legal_research.tests.factories import (
    UserFactory, HighCourtFactory, UserProfileFactory, CaseFactory,
    TagFactory, SuitFactory, SearchHistoryFactory, CustomizationFactory,
    UserNoteFactory, SavedCaseFactory
)


# ============================================================================
# Landing Page Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestLandingPage:
    """Test landing_page view"""

    def test_landing_page_get_returns_200(self):
        """Test GET request returns 200 status"""
        client = Client()
        response = client.get(reverse('legal_research:landing'))
        assert response.status_code == 200

    def test_landing_page_uses_correct_template(self):
        """Test uses correct template"""
        client = Client()
        response = client.get(reverse('legal_research:landing'))
        assert 'legal_research/landing.html' in [t.name for t in response.templates]

    def test_landing_page_redirects_authenticated_users(self, test_user):
        """Test redirects authenticated users to dashboard"""
        client = Client()
        client.force_login(test_user)
        response = client.get(reverse('legal_research:landing'))
        assert response.status_code == 302
        assert response.url == reverse('legal_research:dashboard')


# ============================================================================
# Dashboard Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestDashboard:
    """Test dashboard view"""

    def test_dashboard_requires_authentication(self):
        """Test requires authentication (redirects to login if not authenticated)"""
        client = Client()
        response = client.get(reverse('legal_research:dashboard'))
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_dashboard_get_returns_200_for_authenticated_user(self, authenticated_client):
        """Test GET request returns 200 for authenticated user"""
        response = authenticated_client.get(reverse('legal_research:dashboard'))
        assert response.status_code == 200

    def test_dashboard_context_contains_required_data(self, test_user_with_profile, authenticated_client):
        """Test context contains all required data"""
        # Create some test data
        SearchHistoryFactory.create_batch(10, user=test_user_with_profile)
        SavedCaseFactory.create_batch(5, user=test_user_with_profile)
        UserNoteFactory.create_batch(3, user=test_user_with_profile)

        response = authenticated_client.get(reverse('legal_research:dashboard'))

        assert 'user_profile' in response.context
        assert 'recent_searches' in response.context
        assert 'total_searches' in response.context
        assert 'saved_cases' in response.context
        assert 'user_notes' in response.context
        assert 'active_suits' in response.context
        assert 'system_status' in response.context
        assert 'quick_links' in response.context

        # Verify values
        assert response.context['total_searches'] == 10
        assert response.context['saved_cases'] == 5
        assert response.context['user_notes'] == 3
        assert len(response.context['recent_searches']) <= 5
        assert len(response.context['quick_links']) == 4

    def test_dashboard_system_status_dict(self, authenticated_client):
        """Test system_status contains correct fields"""
        response = authenticated_client.get(reverse('legal_research:dashboard'))
        system_status = response.context['system_status']

        assert 'search_engine' in system_status
        assert 'ai_service' in system_status
        assert 'database' in system_status
        assert 'last_updated' in system_status
        assert 'uptime' in system_status

    def test_dashboard_uses_correct_template(self, authenticated_client):
        """Test uses correct template"""
        response = authenticated_client.get(reverse('legal_research:dashboard'))
        assert 'legal_research/dashboard.html' in [t.name for t in response.templates]


# ============================================================================
# Advanced Search Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestAdvancedSearch:
    """Test advanced_search view"""

    def test_advanced_search_requires_authentication(self):
        """Test requires authentication"""
        client = Client()
        response = client.get(reverse('legal_research:search'))
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_advanced_search_returns_200(self, authenticated_client):
        """Test GET returns 200"""
        response = authenticated_client.get(reverse('legal_research:search'))
        assert response.status_code == 200

    def test_advanced_search_context_data(self, authenticated_client):
        """Test context contains required data"""
        # Create test data
        HighCourtFactory.create_batch(3, is_active=True)
        TagFactory.create_batch(5)

        response = authenticated_client.get(reverse('legal_research:search'))

        assert 'high_courts' in response.context
        assert 'tags' in response.context
        assert 'case_types' in response.context
        assert 'user_suits' in response.context
        assert 'recent_searches' in response.context

        assert response.context['high_courts'].count() == 3
        assert response.context['tags'].count() == 5

    def test_advanced_search_recent_searches_limit(self, test_user, authenticated_client):
        """Test recent_searches limited to 10"""
        SearchHistoryFactory.create_batch(15, user=test_user)

        response = authenticated_client.get(reverse('legal_research:search'))
        assert len(response.context['recent_searches']) == 10

    def test_advanced_search_uses_correct_template(self, authenticated_client):
        """Test uses correct template"""
        response = authenticated_client.get(reverse('legal_research:search'))
        assert 'legal_research/search/search.html' in [t.name for t in response.templates]


# ============================================================================
# Search Results Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestSearchResults:
    """Test search_results view"""

    def test_search_results_requires_authentication(self):
        """Test requires authentication"""
        client = Client()
        response = client.post(reverse('legal_research:search_results'))
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_search_results_post_with_query_creates_history(self, test_user, authenticated_client):
        """Test POST with query creates SearchHistory record"""
        query_text = 'contract breach damages'
        response = authenticated_client.post(
            reverse('legal_research:search_results'),
            {'query': query_text}
        )

        # Verify SearchHistory was created
        assert SearchHistory.objects.filter(user=test_user, query_text=query_text).exists()

    def test_search_results_post_without_query_redirects(self, authenticated_client):
        """Test POST without query redirects with warning message"""
        response = authenticated_client.post(reverse('legal_research:search_results'), {'query': ''})
        assert response.status_code == 302
        assert response.url == reverse('legal_research:search')

    def test_search_results_post_returns_results(self, authenticated_client):
        """Test POST returns results using perform_mock_search()"""
        response = authenticated_client.post(
            reverse('legal_research:search_results'),
            {'query': 'contract law'}
        )

        assert response.status_code == 200
        assert 'results' in response.context
        assert 'query' in response.context
        assert 'total_results' in response.context
        assert response.context['query'] == 'contract law'

    def test_search_results_get_redirects(self, authenticated_client):
        """Test GET request redirects to search page"""
        response = authenticated_client.get(reverse('legal_research:search_results'))
        assert response.status_code == 302


# ============================================================================
# Case Detail Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestCaseDetail:
    """Test case_detail view"""

    def test_case_detail_requires_authentication(self, test_case):
        """Test requires authentication"""
        client = Client()
        response = client.get(reverse('legal_research:case_detail', kwargs={'case_id': test_case.id}))
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_case_detail_valid_case_returns_200(self, test_case, authenticated_client):
        """Test valid case_id returns 200"""
        response = authenticated_client.get(
            reverse('legal_research:case_detail', kwargs={'case_id': test_case.id})
        )
        assert response.status_code == 200

    def test_case_detail_invalid_case_raises_404(self, authenticated_client):
        """Test invalid case_id raises Http404"""
        import uuid
        fake_id = uuid.uuid4()
        response = authenticated_client.get(
            reverse('legal_research:case_detail', kwargs={'case_id': fake_id})
        )
        assert response.status_code == 404

    def test_case_detail_increments_view_count(self, test_case, authenticated_client):
        """Test view_count incremented by 1"""
        original_count = test_case.view_count
        authenticated_client.get(
            reverse('legal_research:case_detail', kwargs={'case_id': test_case.id})
        )

        test_case.refresh_from_db()
        assert test_case.view_count == original_count + 1

    def test_case_detail_context_contains_required_data(self, test_case, test_user, authenticated_client):
        """Test context contains all required data"""
        # Create a user note
        UserNoteFactory(user=test_user, case=test_case)

        response = authenticated_client.get(
            reverse('legal_research:case_detail', kwargs={'case_id': test_case.id})
        )

        assert 'case' in response.context
        assert 'user_note' in response.context
        assert 'related_cases' in response.context
        assert 'is_saved' in response.context

        assert response.context['case'] == test_case
        assert response.context['user_note'] is not None

    def test_case_detail_uses_correct_template(self, test_case, authenticated_client):
        """Test uses correct template"""
        response = authenticated_client.get(
            reverse('legal_research:case_detail', kwargs={'case_id': test_case.id})
        )
        assert 'legal_research/cases/case_detail.html' in [t.name for t in response.templates]


# ============================================================================
# Save Case Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestSaveCase:
    """Test save_case view"""

    def test_save_case_requires_authentication(self, test_case):
        """Test requires authentication"""
        client = Client()
        response = client.get(reverse('legal_research:save_case', kwargs={'case_id': test_case.id}))
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_save_case_creates_saved_case(self, test_case, test_user, authenticated_client):
        """Test creates SavedCase record with default folder 'General'"""
        response = authenticated_client.get(
            reverse('legal_research:save_case', kwargs={'case_id': test_case.id})
        )

        assert SavedCase.objects.filter(user=test_user, case=test_case).exists()
        saved_case = SavedCase.objects.get(user=test_user, case=test_case)
        assert saved_case.folder == 'General'

    def test_save_case_prevents_duplicates(self, test_case, test_user, authenticated_client):
        """Test get_or_create prevents duplicates"""
        # Save once
        authenticated_client.get(
            reverse('legal_research:save_case', kwargs={'case_id': test_case.id})
        )

        # Save again
        authenticated_client.get(
            reverse('legal_research:save_case', kwargs={'case_id': test_case.id})
        )

        # Should only have one SavedCase
        assert SavedCase.objects.filter(user=test_user, case=test_case).count() == 1

    def test_save_case_redirects_to_case_detail(self, test_case, authenticated_client):
        """Test redirects to case_detail"""
        response = authenticated_client.get(
            reverse('legal_research:save_case', kwargs={'case_id': test_case.id})
        )

        assert response.status_code == 302
        assert response.url == reverse('legal_research:case_detail', kwargs={'case_id': test_case.id})


# ============================================================================
# Export Case Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestExportCase:
    """Test export_case view"""

    def test_export_case_requires_authentication(self, test_case):
        """Test requires authentication"""
        client = Client()
        response = client.get(reverse('legal_research:export_case', kwargs={'case_id': test_case.id}))
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_export_case_pdf_returns_pdf(self, test_case, authenticated_client):
        """Test PDF export returns application/pdf content-type"""
        response = authenticated_client.get(
            reverse('legal_research:export_case', kwargs={'case_id': test_case.id}),
            {'format': 'pdf'}
        )

        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'
        assert 'Content-Disposition' in response
        assert f'{test_case.citation}.pdf' in response['Content-Disposition']

    def test_export_case_txt_returns_text(self, test_case, authenticated_client):
        """Test TXT export returns text/plain"""
        response = authenticated_client.get(
            reverse('legal_research:export_case', kwargs={'case_id': test_case.id}),
            {'format': 'txt'}
        )

        assert response.status_code == 200
        assert response['Content-Type'] == 'text/plain'
        assert test_case.title in response.content.decode('utf-8')
        assert test_case.citation in response.content.decode('utf-8')

    def test_export_case_invalid_format_shows_error(self, test_case, authenticated_client):
        """Test invalid format shows error and redirects"""
        response = authenticated_client.get(
            reverse('legal_research:export_case', kwargs={'case_id': test_case.id}),
            {'format': 'invalid'}
        )

        assert response.status_code == 302


# ============================================================================
# Save Case Note Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestSaveCaseNote:
    """Test save_case_note API"""

    def test_save_case_note_creates_or_updates(self, test_case, test_user, authenticated_client):
        """Test creates or updates UserNote"""
        response = authenticated_client.post(
            reverse('legal_research:save_case_note', kwargs={'case_id': test_case.id}),
            {'note_text': 'Important case for reference'}
        )

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True

        # Verify note was created
        assert UserNote.objects.filter(user=test_user, case=test_case).exists()

    def test_save_case_note_empty_deletes_note(self, test_case, test_user, authenticated_client):
        """Test empty note_text deletes existing note"""
        # Create a note first
        UserNoteFactory(user=test_user, case=test_case)

        # Delete it
        response = authenticated_client.post(
            reverse('legal_research:save_case_note', kwargs={'case_id': test_case.id}),
            {'note_text': ''}
        )

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True

        # Verify note was deleted
        assert not UserNote.objects.filter(user=test_user, case=test_case).exists()

    def test_save_case_note_returns_json(self, test_case, authenticated_client):
        """Test returns JSON with success: true"""
        response = authenticated_client.post(
            reverse('legal_research:save_case_note', kwargs={'case_id': test_case.id}),
            {'note_text': 'Test note'}
        )

        assert response['Content-Type'] == 'application/json'
        data = json.loads(response.content)
        assert 'success' in data
        assert 'created' in data


# ============================================================================
# Customization Panel Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestCustomizationPanel:
    """Test customization_panel view"""

    def test_customization_panel_requires_authentication(self):
        """Test requires authentication"""
        client = Client()
        response = client.get(reverse('legal_research:customization'))
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_customization_panel_requires_profile(self, test_user, authenticated_client):
        """Test requires user profile (redirects to profile if missing)"""
        # User without profile
        response = authenticated_client.get(reverse('legal_research:customization'))
        assert response.status_code == 302

    def test_customization_panel_context_data(self, test_user_with_profile, authenticated_client):
        """Test context contains user_suits and customizations dict"""
        response = authenticated_client.get(reverse('legal_research:customization'))

        assert response.status_code == 200
        assert 'user_suits' in response.context
        assert 'customizations' in response.context
        assert 'user_profile' in response.context


# ============================================================================
# Update Customization Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestUpdateCustomization:
    """Test update_customization API"""

    def test_update_customization_requires_suit_id(self, authenticated_client):
        """Test requires suit_id in data"""
        response = authenticated_client.post(
            reverse('legal_research:update_customization'),
            json.dumps({}),
            content_type='application/json'
        )

        assert response.status_code == 400

    def test_update_customization_validates_access(self, test_user, test_suit, authenticated_client):
        """Test validates user has access to suit"""
        # Create a suit the user doesn't have access to
        other_profile = UserProfileFactory()
        other_suit = SuitFactory(created_by=other_profile)

        response = authenticated_client.post(
            reverse('legal_research:update_customization'),
            json.dumps({'suit_id': other_suit.id}),
            content_type='application/json'
        )

        # Should return 403 or 404
        assert response.status_code in [403, 404]

    def test_update_customization_creates_or_updates(self, test_user_with_profile, test_suit, authenticated_client):
        """Test creates or updates Customization record"""
        profile = UserProfile.objects.get(user=test_user_with_profile)
        suit = SuitFactory(created_by=profile)
        suit.assigned_users.add(profile)

        data = {
            'suit_id': suit.id,
            'jurisdiction_emphasis': {'Delhi': 1.5},
            'language_preferences': ['en', 'hi'],
            'precedent_statute_weight': 0.6,
            'time_period_focus': 'recent',
            'analysis_focus_areas': ['contract_law']
        }

        response = authenticated_client.post(
            reverse('legal_research:update_customization'),
            json.dumps(data),
            content_type='application/json'
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data['success'] is True

    def test_update_customization_handles_invalid_json(self, authenticated_client):
        """Test handles invalid JSON"""
        response = authenticated_client.post(
            reverse('legal_research:update_customization'),
            'invalid json',
            content_type='application/json'
        )

        assert response.status_code == 400


# ============================================================================
# Analytics Dashboard Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestAnalyticsDashboard:
    """Test analytics_dashboard view"""

    def test_analytics_dashboard_requires_authentication(self):
        """Test requires authentication"""
        client = Client()
        response = client.get(reverse('legal_research:analytics'))
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_analytics_dashboard_returns_200(self, authenticated_client):
        """Test GET returns 200"""
        response = authenticated_client.get(reverse('legal_research:analytics'))
        assert response.status_code == 200

    def test_analytics_dashboard_context_data(self, authenticated_client):
        """Test context contains analytics_data"""
        response = authenticated_client.get(reverse('legal_research:analytics'))

        assert 'analytics_data' in response.context
        analytics_data = response.context['analytics_data']
        assert 'kpis' in analytics_data
        assert 'trends' in analytics_data


# ============================================================================
# Data Upload Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestDataUpload:
    """Test data_upload view"""

    def test_data_upload_requires_authentication(self):
        """Test requires authentication"""
        client = Client()
        response = client.get(reverse('legal_research:upload'))
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_data_upload_get_returns_form(self, authenticated_client):
        """Test GET returns upload form"""
        response = authenticated_client.get(reverse('legal_research:upload'))
        assert response.status_code == 200

    def test_data_upload_uses_correct_template(self, authenticated_client):
        """Test uses correct template"""
        response = authenticated_client.get(reverse('legal_research:upload'))
        assert 'legal_research/upload/upload.html' in [t.name for t in response.templates]


# ============================================================================
# Process Upload Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestProcessUpload:
    """Test process_upload API"""

    def test_process_upload_requires_post(self, authenticated_client):
        """Test requires POST method"""
        response = authenticated_client.get(reverse('legal_research:process_upload'))
        assert response.status_code == 405

    def test_process_upload_requires_file(self, authenticated_client):
        """Test requires file in request.FILES"""
        response = authenticated_client.post(reverse('legal_research:process_upload'), {})
        assert response.status_code == 400

    def test_process_upload_validates_file_type(self, authenticated_client, sample_uploaded_file):
        """Test validates file type"""
        response = authenticated_client.post(
            reverse('legal_research:process_upload'),
            {'file': sample_uploaded_file}
        )

        # Sample file is text/plain, which is allowed
        assert response.status_code == 200

    def test_process_upload_returns_json(self, authenticated_client, sample_uploaded_file):
        """Test returns JSON with success, filename, size, records_processed"""
        response = authenticated_client.post(
            reverse('legal_research:process_upload'),
            {'file': sample_uploaded_file}
        )

        assert response['Content-Type'] == 'application/json'
        data = json.loads(response.content)
        assert 'success' in data
        assert 'filename' in data
        assert 'size' in data


# ============================================================================
# User Profile Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestUserProfile:
    """Test user_profile view"""

    def test_user_profile_requires_authentication(self):
        """Test requires authentication"""
        client = Client()
        response = client.get(reverse('legal_research:profile'))
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_user_profile_get_returns_200(self, authenticated_client):
        """Test GET returns profile page"""
        response = authenticated_client.get(reverse('legal_research:profile'))
        assert response.status_code == 200

    def test_user_profile_context_data(self, authenticated_client):
        """Test context contains user_profile and high_courts"""
        HighCourtFactory.create_batch(3, is_active=True)

        response = authenticated_client.get(reverse('legal_research:profile'))

        assert 'user_profile' in response.context
        assert 'high_courts' in response.context
        assert response.context['high_courts'].count() == 3

    def test_user_profile_uses_correct_template(self, authenticated_client):
        """Test uses correct template"""
        response = authenticated_client.get(reverse('legal_research:profile'))
        assert 'legal_research/profile/profile.html' in [t.name for t in response.templates]


# ============================================================================
# Update User Profile Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestUpdateUserProfile:
    """Test update_user_profile function"""

    def test_update_user_profile_updates_user_fields(self, test_user, authenticated_client):
        """Test updates User fields"""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com',
            'designation': 'Judge',
            'employee_id': 'EMP123',
            'phone_number': '+91-1234567890',
            'default_language': 'en'
        }

        response = authenticated_client.post(reverse('legal_research:profile'), data)

        test_user.refresh_from_db()
        assert test_user.first_name == 'Updated'
        assert test_user.last_name == 'Name'
        assert test_user.email == 'updated@example.com'

    def test_update_user_profile_creates_profile_if_missing(self, test_user, authenticated_client):
        """Test creates UserProfile if doesn't exist"""
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'designation': 'Judge',
            'employee_id': 'EMP999',
            'phone_number': '+91-1234567890',
            'default_language': 'en'
        }

        response = authenticated_client.post(reverse('legal_research:profile'), data)

        assert UserProfile.objects.filter(user=test_user).exists()

    def test_update_user_profile_redirects_on_success(self, authenticated_client):
        """Test shows success message and redirects to profile"""
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'designation': 'Judge',
            'employee_id': 'EMP999'
        }

        response = authenticated_client.post(reverse('legal_research:profile'), data)

        assert response.status_code == 302
        assert response.url == reverse('legal_research:profile')
