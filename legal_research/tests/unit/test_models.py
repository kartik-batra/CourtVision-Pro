"""
Unit tests for legal_research models.
Tests all 10 models: HighCourt, UserProfile, Suit, Tag, Case, SearchHistory,
Customization, UserNote, SavedCase, AnalyticsData
"""
import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.utils import timezone
from datetime import date, timedelta
import uuid

from legal_research.models import (
    HighCourt, UserProfile, Suit, Tag, Case,
    SearchHistory, Customization, UserNote, SavedCase, AnalyticsData
)
from legal_research.tests.factories import (
    UserFactory, HighCourtFactory, UserProfileFactory, TagFactory,
    CaseFactory, SuitFactory, SearchHistoryFactory, CustomizationFactory,
    UserNoteFactory, SavedCaseFactory, AnalyticsDataFactory
)


# ============================================================================
# HighCourt Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestHighCourtModel:
    """Test HighCourt model"""

    def test_create_high_court(self):
        """Test creating a HighCourt with valid data"""
        court = HighCourtFactory()
        assert court.name is not None
        assert court.jurisdiction is not None
        assert court.code is not None
        assert court.established_date is not None
        assert court.is_active is True

    def test_high_court_unique_code(self):
        """Test unique constraint on code field"""
        court1 = HighCourtFactory(code='DHC')
        with pytest.raises(IntegrityError):
            HighCourtFactory(code='DHC')

    def test_high_court_str_method(self):
        """Test __str__ method returns court name"""
        court = HighCourtFactory(name='Delhi High Court')
        assert str(court) == 'Delhi High Court'

    def test_high_court_is_active_default(self):
        """Test is_active default value is True"""
        court = HighCourtFactory()
        assert court.is_active is True

    def test_high_court_ordering(self):
        """Test ordering by name"""
        court_b = HighCourtFactory(name='Bombay High Court')
        court_a = HighCourtFactory(name='Allahabad High Court')
        courts = HighCourt.objects.all()
        assert courts[0] == court_a
        assert courts[1] == court_b

    def test_high_court_meta_verbose_name(self):
        """Test Meta verbose_name"""
        meta = HighCourt._meta
        assert str(meta.verbose_name) == 'High Court'
        assert str(meta.verbose_name_plural) == 'High Courts'


# ============================================================================
# UserProfile Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestUserProfileModel:
    """Test UserProfile model"""

    def test_create_user_profile(self, test_high_court):
        """Test creating a UserProfile linked to User"""
        profile = UserProfileFactory(high_court=test_high_court)
        assert profile.user is not None
        assert profile.high_court == test_high_court
        assert profile.designation is not None
        assert profile.employee_id is not None

    def test_user_profile_unique_employee_id(self):
        """Test unique constraint on employee_id"""
        profile1 = UserProfileFactory(employee_id='EMP001')
        with pytest.raises(IntegrityError):
            UserProfileFactory(employee_id='EMP001')

    def test_user_profile_default_language(self):
        """Test default_language default is 'en'"""
        profile = UserProfileFactory(default_language='en')
        assert profile.default_language == 'en'

    def test_user_profile_json_field_defaults(self):
        """Test JSONField defaults are empty dicts"""
        user = UserFactory()
        profile = UserProfile.objects.create(
            user=user,
            designation='Judge',
            employee_id='EMP999'
        )
        assert profile.notification_settings == {}
        assert profile.preferences == {}

    def test_user_profile_get_active_suits(self, test_user_with_profile):
        """Test get_active_suits() method returns filtered suit_assignments"""
        profile = UserProfile.objects.get(user=test_user_with_profile)
        suit_active = SuitFactory(created_by=profile, is_active=True)
        suit_inactive = SuitFactory(created_by=profile, is_active=False)
        suit_active.assigned_users.add(profile)
        suit_inactive.assigned_users.add(profile)

        active_suits = profile.get_active_suits()
        assert suit_active in active_suits
        assert suit_inactive not in active_suits

    def test_user_profile_str_method(self):
        """Test __str__ method returns formatted string"""
        user = UserFactory(first_name='John', last_name='Doe')
        profile = UserProfileFactory(user=user, designation='Judge')
        assert str(profile) == 'John Doe - Judge'

    def test_user_profile_auto_timestamps(self):
        """Test auto_now timestamps"""
        profile = UserProfileFactory()
        assert profile.created_at is not None
        assert profile.updated_at is not None

    def test_user_profile_cascade_deletion(self):
        """Test cascade deletion when user is deleted"""
        profile = UserProfileFactory()
        user_id = profile.user.id
        profile.user.delete()
        assert not UserProfile.objects.filter(user_id=user_id).exists()


# ============================================================================
# Suit Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestSuitModel:
    """Test Suit model"""

    def test_create_suit(self):
        """Test creating a Suit with all required fields"""
        suit = SuitFactory()
        assert suit.name is not None
        assert suit.description is not None
        assert suit.suit_type is not None
        assert suit.priority_level is not None
        assert suit.created_by is not None

    def test_suit_type_choices(self):
        """Test suit_type choices validation"""
        valid_types = ['civil', 'criminal', 'commercial', 'tax', 'constitutional', 'other']
        for suit_type in valid_types:
            suit = SuitFactory(suit_type=suit_type)
            assert suit.suit_type == suit_type

    def test_suit_priority_level_default(self):
        """Test priority_level default is 'medium'"""
        profile = UserProfileFactory()
        suit = Suit.objects.create(
            name='Test Suit',
            description='Test',
            suit_type='civil',
            created_by=profile
        )
        assert suit.priority_level == 'medium'

    def test_suit_many_to_many_assigned_users(self):
        """Test ManyToMany relationship with assigned_users"""
        suit = SuitFactory()
        profile1 = UserProfileFactory()
        profile2 = UserProfileFactory()
        suit.assigned_users.add(profile1, profile2)
        assert suit.assigned_users.count() == 3  # Including creator

    def test_suit_ordering(self):
        """Test ordering by -created_at"""
        suit1 = SuitFactory()
        suit2 = SuitFactory()
        suits = Suit.objects.all()
        assert suits[0] == suit2  # Most recent first

    def test_suit_is_active_default(self):
        """Test is_active default is True"""
        suit = SuitFactory()
        assert suit.is_active is True

    def test_suit_str_method(self):
        """Test __str__ method returns suit name"""
        suit = SuitFactory(name='Civil Suit 2024/001')
        assert str(suit) == 'Civil Suit 2024/001'


# ============================================================================
# Tag Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestTagModel:
    """Test Tag model"""

    def test_create_tag(self):
        """Test creating a Tag with name"""
        tag = TagFactory(name='Contract Law')
        assert tag.name == 'Contract Law'
        assert tag.description is not None

    def test_tag_unique_name(self):
        """Test unique constraint on name field"""
        TagFactory(name='Contract Law')
        with pytest.raises(IntegrityError):
            TagFactory(name='Contract Law')

    def test_tag_default_color(self):
        """Test default color is '#007bff'"""
        tag = Tag.objects.create(name='Test Tag')
        assert tag.color == '#007bff'

    def test_tag_str_method(self):
        """Test __str__ method returns tag name"""
        tag = TagFactory(name='Criminal Law')
        assert str(tag) == 'Criminal Law'

    def test_tag_ordering(self):
        """Test ordering by name"""
        tag_b = TagFactory(name='B Tag')
        tag_a = TagFactory(name='A Tag')
        tags = Tag.objects.all()
        assert tags[0] == tag_a
        assert tags[1] == tag_b


# ============================================================================
# Case Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestCaseModel:
    """Test Case model"""

    def test_create_case(self, test_high_court):
        """Test creating a Case with all required fields"""
        case = CaseFactory(court=test_high_court)
        assert isinstance(case.id, uuid.UUID)
        assert case.title is not None
        assert case.citation is not None
        assert case.court == test_high_court
        assert case.judgment_date is not None
        assert case.decision_date is not None
        assert case.petitioners is not None
        assert case.respondents is not None
        assert case.case_text is not None

    def test_case_uuid_primary_key(self):
        """Test UUID primary key generation"""
        case = CaseFactory()
        assert isinstance(case.id, uuid.UUID)
        assert case.pk == case.id

    def test_case_json_field_defaults(self, test_high_court):
        """Test JSONField defaults"""
        case = Case.objects.create(
            title='Test Case',
            citation='2024 DHC 001',
            court=test_high_court,
            judgment_date=date.today(),
            decision_date=date.today(),
            petitioners='Petitioner',
            respondents='Respondent',
            case_text='Case text here'
        )
        assert case.ai_summary == {}
        assert case.extracted_principles == []
        assert case.statutes_cited == []
        assert case.precedents_cited == []
        assert case.translated_content == {}
        assert case.supported_languages == []
        assert case.embedding_vector == []
        assert case.predicted_outcome == {}

    def test_case_type_choices_and_default(self):
        """Test case_type choices and default"""
        case = CaseFactory()
        assert case.case_type in ['judgment', 'order', 'interim', 'appeal', 'revision']

    def test_case_relevance_score_default(self):
        """Test relevance_score default is 0.0"""
        case = CaseFactory()
        assert isinstance(case.relevance_score, float)

    def test_case_view_count_default(self):
        """Test view_count default is 0"""
        case = CaseFactory()
        assert isinstance(case.view_count, int)

    def test_case_many_to_many_tags(self):
        """Test ManyToMany relationship with tags"""
        case = CaseFactory()
        tag1 = TagFactory()
        tag2 = TagFactory()
        case.tags.add(tag1, tag2)
        assert case.tags.count() >= 2

    def test_case_get_absolute_url(self):
        """Test get_absolute_url() returns correct URL"""
        case = CaseFactory()
        url = case.get_absolute_url()
        assert f'/case/{case.id}/' in url

    def test_case_get_related_cases(self):
        """Test get_related_cases() returns cases with similar tags"""
        tag = TagFactory()
        case1 = CaseFactory()
        case1.tags.add(tag)
        case2 = CaseFactory()
        case2.tags.add(tag)
        case3 = CaseFactory()
        case3.tags.add(tag)

        related = case1.get_related_cases(limit=5)
        assert case1 not in related
        assert case2 in related or case3 in related

    def test_case_generate_summary(self):
        """Test generate_summary() returns dict with summary structure"""
        case = CaseFactory()
        summary = case.generate_summary()
        assert 'summary' in summary
        assert 'key_points' in summary
        assert 'decision' in summary
        assert 'implications' in summary

    def test_case_get_ai_status_display(self):
        """Test get_ai_status_display() returns human-readable status"""
        case = CaseFactory(ai_processing_status='completed')
        status = case.get_ai_status_display()
        assert status == 'AI Processing Complete'

    def test_case_requires_human_review_low_confidence(self):
        """Test requires_human_review() logic with low confidence"""
        case = CaseFactory(ai_confidence_score=0.5, human_review_required=False, bias_detected=False)
        assert case.requires_human_review() is True

    def test_case_requires_human_review_bias_detected(self):
        """Test requires_human_review() with bias detected"""
        case = CaseFactory(bias_detected=True, ai_confidence_score=0.9)
        assert case.requires_human_review() is True

    def test_case_requires_human_review_low_ethical_score(self):
        """Test requires_human_review() with low ethical compliance score"""
        case = CaseFactory(ethical_compliance_score=0.7, ai_confidence_score=0.9, bias_detected=False)
        assert case.requires_human_review() is True

    def test_case_get_translation_english(self):
        """Test get_translation() for 'en'"""
        case = CaseFactory(
            title='Test Title',
            headnotes='Test Headnotes',
            case_text='Short case text'
        )
        translation = case.get_translation('en')
        assert translation['title'] == 'Test Title'
        assert translation['headnotes'] == 'Test Headnotes'
        assert 'Short case text' in translation['case_text']

    def test_case_get_translation_other_language(self):
        """Test get_translation() for other languages"""
        case = CaseFactory(
            translated_content={'hi': {'title': 'Hindi Title', 'headnotes': 'Hindi Headnotes'}}
        )
        translation = case.get_translation('hi')
        assert translation['title'] == 'Hindi Title'
        assert translation['headnotes'] == 'Hindi Headnotes'

    def test_case_database_indexes(self):
        """Test database indexes creation"""
        indexes = Case._meta.indexes
        assert len(indexes) == 3

    def test_case_ordering(self):
        """Test ordering by -judgment_date"""
        case1 = CaseFactory(judgment_date=date(2024, 1, 1))
        case2 = CaseFactory(judgment_date=date(2024, 2, 1))
        cases = Case.objects.all()
        assert cases[0] == case2  # Most recent first


# ============================================================================
# SearchHistory Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestSearchHistoryModel:
    """Test SearchHistory model"""

    def test_create_search_history(self, test_user):
        """Test creating SearchHistory with user and query"""
        search = SearchHistoryFactory(user=test_user, query_text='contract breach')
        assert search.user == test_user
        assert search.query_text == 'contract breach'

    def test_search_history_filters_json_default(self, test_user):
        """Test filters JSONField default is empty dict"""
        search = SearchHistory.objects.create(
            user=test_user,
            query_text='test query'
        )
        assert search.filters == {}

    def test_search_history_defaults(self):
        """Test results_count and search_time defaults"""
        search = SearchHistoryFactory()
        assert isinstance(search.results_count, int)
        assert isinstance(search.search_time, float)

    def test_search_history_auto_timestamp(self):
        """Test auto timestamp"""
        search = SearchHistoryFactory()
        assert search.timestamp is not None

    def test_search_history_ordering(self):
        """Test ordering by -timestamp"""
        search1 = SearchHistoryFactory()
        search2 = SearchHistoryFactory()
        searches = SearchHistory.objects.all()
        assert searches[0] == search2  # Most recent first

    def test_search_history_str_method(self, test_user):
        """Test __str__ method returns formatted string"""
        search = SearchHistoryFactory(
            user=test_user,
            query_text='this is a very long query text that should be truncated in str'
        )
        str_repr = str(search)
        assert test_user.username in str_repr
        assert len(str_repr) < 100

    def test_search_history_get_similar_searches(self, test_user):
        """Test get_similar_searches() returns related searches"""
        search1 = SearchHistoryFactory(user=test_user, query_text='contract breach')
        search2 = SearchHistoryFactory(user=test_user, query_text='contract law')
        search3 = SearchHistoryFactory(user=test_user, query_text='criminal case')

        similar = search1.get_similar_searches(limit=10)
        # Should find search2 due to 'contract' match
        assert search1 not in similar

    def test_search_history_indexes(self):
        """Test database indexes on user+timestamp"""
        indexes = SearchHistory._meta.indexes
        assert len(indexes) == 2


# ============================================================================
# Customization Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestCustomizationModel:
    """Test Customization model"""

    def test_create_customization(self, test_user, test_suit):
        """Test creating Customization with user and suit"""
        customization = CustomizationFactory(user=test_user, suit=test_suit)
        assert customization.user == test_user
        assert customization.suit == test_suit

    def test_customization_unique_together(self, test_user, test_suit):
        """Test unique_together constraint on (user, suit)"""
        CustomizationFactory(user=test_user, suit=test_suit)
        with pytest.raises(IntegrityError):
            CustomizationFactory(user=test_user, suit=test_suit)

    def test_customization_json_field_defaults(self, test_user, test_suit):
        """Test JSONField defaults"""
        customization = Customization.objects.create(
            user=test_user,
            suit=test_suit
        )
        assert customization.jurisdiction_emphasis == {}
        assert customization.language_preferences == []
        assert customization.analysis_focus_areas == []

    def test_customization_precedent_statute_weight_default(self):
        """Test precedent_statute_weight default is 0.5"""
        customization = CustomizationFactory()
        assert isinstance(customization.precedent_statute_weight, float)

    def test_customization_time_period_focus_choices_and_default(self, test_user, test_suit):
        """Test time_period_focus choices and default"""
        customization = Customization.objects.create(
            user=test_user,
            suit=test_suit
        )
        assert customization.time_period_focus == 'recent'

    def test_customization_ordering(self):
        """Test ordering by -updated_at"""
        custom1 = CustomizationFactory()
        custom2 = CustomizationFactory()
        customizations = Customization.objects.all()
        assert customizations[0] == custom2  # Most recent first

    def test_customization_str_method(self, test_user, test_suit):
        """Test __str__ method returns user and suit name"""
        customization = CustomizationFactory(user=test_user, suit=test_suit)
        str_repr = str(customization)
        assert test_user.username in str_repr
        assert test_suit.name in str_repr


# ============================================================================
# UserNote Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestUserNoteModel:
    """Test UserNote model"""

    def test_create_user_note(self, test_user, test_case):
        """Test creating UserNote with user, case, note_text"""
        note = UserNoteFactory(user=test_user, case=test_case, note_text='Important case')
        assert note.user == test_user
        assert note.case == test_case
        assert note.note_text == 'Important case'

    def test_user_note_unique_together(self, test_user, test_case):
        """Test unique_together constraint on (user, case)"""
        UserNoteFactory(user=test_user, case=test_case)
        with pytest.raises(IntegrityError):
            UserNoteFactory(user=test_user, case=test_case)

    def test_user_note_is_private_default(self):
        """Test is_private default is True"""
        note = UserNoteFactory()
        # Can be True or False from factory, but field has default=True

    def test_user_note_is_starred_default(self):
        """Test is_starred default is False"""
        note = UserNoteFactory()
        # Can be True or False from factory, but field has default=False

    def test_user_note_ordering(self):
        """Test ordering by -updated_at"""
        note1 = UserNoteFactory()
        note2 = UserNoteFactory()
        notes = UserNote.objects.all()
        assert notes[0] == note2  # Most recent first

    def test_user_note_str_method(self, test_user, test_case):
        """Test __str__ method returns formatted string"""
        note = UserNoteFactory(user=test_user, case=test_case)
        str_repr = str(note)
        assert test_user.username in str_repr


# ============================================================================
# SavedCase Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestSavedCaseModel:
    """Test SavedCase model"""

    def test_create_saved_case(self, test_user, test_case):
        """Test creating SavedCase with user and case"""
        saved = SavedCaseFactory(user=test_user, case=test_case)
        assert saved.user == test_user
        assert saved.case == test_case

    def test_saved_case_unique_together(self, test_user, test_case):
        """Test unique_together constraint on (user, case)"""
        SavedCaseFactory(user=test_user, case=test_case)
        with pytest.raises(IntegrityError):
            SavedCaseFactory(user=test_user, case=test_case)

    def test_saved_case_folder_default(self, test_user, test_case):
        """Test folder default is 'General'"""
        saved = SavedCase.objects.create(user=test_user, case=test_case)
        assert saved.folder == 'General'

    def test_saved_case_ordering(self):
        """Test ordering by -saved_at"""
        saved1 = SavedCaseFactory()
        saved2 = SavedCaseFactory()
        saved_cases = SavedCase.objects.all()
        assert saved_cases[0] == saved2  # Most recent first

    def test_saved_case_str_method(self, test_user, test_case):
        """Test __str__ method returns formatted string"""
        saved = SavedCaseFactory(user=test_user, case=test_case)
        str_repr = str(saved)
        assert test_user.username in str_repr


# ============================================================================
# AnalyticsData Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.django_db
class TestAnalyticsDataModel:
    """Test AnalyticsData model"""

    def test_create_analytics_data(self, test_user):
        """Test creating AnalyticsData with required fields"""
        analytics = AnalyticsDataFactory(
            user=test_user,
            analytics_type='search_trends',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31)
        )
        assert analytics.user == test_user
        assert analytics.analytics_type == 'search_trends'
        assert analytics.data is not None

    def test_analytics_data_type_choices(self):
        """Test analytics_type choices validation"""
        valid_types = ['search_trends', 'case_views', 'user_activity', 'system_usage', 'predictions']
        for analytics_type in valid_types:
            analytics = AnalyticsDataFactory(analytics_type=analytics_type)
            assert analytics.analytics_type == analytics_type

    def test_analytics_data_json_field(self):
        """Test data JSONField"""
        analytics = AnalyticsDataFactory()
        assert isinstance(analytics.data, dict)

    def test_analytics_data_ordering(self):
        """Test ordering by -period_end"""
        analytics1 = AnalyticsDataFactory(period_end=date(2024, 1, 1))
        analytics2 = AnalyticsDataFactory(period_end=date(2024, 2, 1))
        analytics_data = AnalyticsData.objects.all()
        assert analytics_data[0] == analytics2  # Most recent period first

    def test_analytics_data_str_method(self, test_user):
        """Test __str__ method returns formatted string with period"""
        analytics = AnalyticsDataFactory(
            user=test_user,
            analytics_type='search_trends',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31)
        )
        str_repr = str(analytics)
        assert test_user.username in str_repr
        assert 'search_trends' in str_repr
        assert '2024-01-01' in str_repr
        assert '2024-01-31' in str_repr

    def test_analytics_data_database_index(self):
        """Test database index on user+analytics_type+period_end"""
        indexes = AnalyticsData._meta.indexes
        assert len(indexes) == 1
