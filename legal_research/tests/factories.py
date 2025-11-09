"""
Factory Boy factories for generating test data.
"""
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import random
import uuid

from legal_research.models import (
    HighCourt, UserProfile, Suit, Tag, Case,
    SearchHistory, Customization, UserNote, SavedCase, AnalyticsData
)

fake = Faker()


class UserFactory(DjangoModelFactory):
    """Factory for Django User model"""

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_staff = False
    is_superuser = False

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """Set password after creating user"""
        if not create:
            return
        password = extracted or 'testpass123'
        obj.set_password(password)
        obj.save()


class AdminUserFactory(UserFactory):
    """Factory for admin users"""
    is_staff = True
    is_superuser = True
    username = factory.Sequence(lambda n: f'admin{n}')


class HighCourtFactory(DjangoModelFactory):
    """Factory for HighCourt model"""

    class Meta:
        model = HighCourt

    name = factory.Faker('random_element', elements=[
        'Delhi High Court',
        'Bombay High Court',
        'Calcutta High Court',
        'Madras High Court',
        'Punjab and Haryana High Court',
        'Allahabad High Court',
        'Karnataka High Court',
        'Kerala High Court',
        'Gujarat High Court',
        'Rajasthan High Court'
    ])
    jurisdiction = factory.LazyAttribute(lambda obj: obj.name.split(' High')[0])
    code = factory.Sequence(lambda n: f'HC{n:02d}')
    established_date = factory.Faker('date_between', start_date='-100y', end_date='-10y')
    is_active = True


class UserProfileFactory(DjangoModelFactory):
    """Factory for UserProfile model"""

    class Meta:
        model = UserProfile

    user = factory.SubFactory(UserFactory)
    high_court = factory.SubFactory(HighCourtFactory)
    designation = factory.Faker('random_element', elements=[
        'Judge',
        'Additional Judge',
        'District Judge',
        'Civil Judge',
        'Magistrate',
        'Legal Researcher',
        'Law Clerk'
    ])
    employee_id = factory.Sequence(lambda n: f'EMP{n:05d}')
    phone_number = factory.Faker('phone_number')
    default_language = factory.Faker('random_element', elements=['en', 'hi', 'ta', 'te'])
    notification_settings = factory.LazyFunction(lambda: {
        'email': True,
        'sms': random.choice([True, False]),
        'push': random.choice([True, False]),
        'frequency': random.choice(['immediate', 'daily', 'weekly'])
    })
    preferences = factory.LazyFunction(lambda: {
        'theme': random.choice(['light', 'dark', 'auto']),
        'results_per_page': random.choice([10, 20, 50]),
        'default_search_type': random.choice(['keyword', 'semantic', 'hybrid'])
    })


class TagFactory(DjangoModelFactory):
    """Factory for Tag model"""

    class Meta:
        model = Tag
        django_get_or_create = ('name',)

    name = factory.Faker('random_element', elements=[
        'Contract Law',
        'Criminal Law',
        'Constitutional Law',
        'Tax Law',
        'Corporate Law',
        'Property Law',
        'Family Law',
        'Labor Law',
        'Environmental Law',
        'Intellectual Property',
        'Administrative Law',
        'Tort Law',
        'Evidence',
        'Procedure',
        'Jurisdiction'
    ])
    description = factory.Faker('sentence')
    color = factory.Faker('hex_color')


class CaseFactory(DjangoModelFactory):
    """Factory for Case model"""

    class Meta:
        model = Case

    id = factory.LazyFunction(uuid.uuid4)
    title = factory.LazyAttribute(lambda obj: f'{fake.name()} vs {fake.name()}')
    citation = factory.LazyAttribute(lambda obj: f'{fake.year()} {fake.random_element(["SCC", "DHC", "BHC", "MHC"])} {fake.random_int(1, 999)}')
    court = factory.SubFactory(HighCourtFactory)
    bench = factory.Faker('random_element', elements=[
        'Single Bench',
        'Division Bench',
        'Full Bench',
        'Constitution Bench'
    ])
    judgment_date = factory.Faker('date_between', start_date='-5y', end_date='today')
    decision_date = factory.LazyAttribute(lambda obj: obj.judgment_date + timedelta(days=random.randint(1, 30)))
    petitioners = factory.LazyAttribute(lambda obj: ', '.join([fake.name() for _ in range(random.randint(1, 3))]))
    respondents = factory.LazyAttribute(lambda obj: ', '.join([fake.name() for _ in range(random.randint(1, 3))]))
    case_text = factory.Faker('text', max_nb_chars=5000)
    headnotes = factory.Faker('text', max_nb_chars=500)

    ai_summary = factory.LazyFunction(lambda: {
        'summary': fake.paragraph(),
        'key_points': [fake.sentence() for _ in range(3)],
        'decision': fake.sentence(),
        'implications': fake.paragraph()
    })
    extracted_principles = factory.LazyFunction(lambda: [
        {
            'principle': fake.sentence(),
            'context': fake.paragraph(),
            'confidence': round(random.uniform(0.7, 0.99), 2)
        }
        for _ in range(random.randint(2, 5))
    ])
    statutes_cited = factory.LazyFunction(lambda: [
        {
            'statute': fake.random_element([
                'Indian Contract Act, 1872',
                'Indian Penal Code, 1860',
                'Constitution of India',
                'Code of Civil Procedure, 1908',
                'Code of Criminal Procedure, 1973'
            ]),
            'section': f'Section {random.randint(1, 500)}'
        }
        for _ in range(random.randint(1, 5))
    ])
    precedents_cited = factory.LazyFunction(lambda: [
        {
            'case_id': str(uuid.uuid4()),
            'citation': f'{fake.year()} SCC {random.randint(1, 999)}',
            'relevance': round(random.uniform(0.6, 0.95), 2)
        }
        for _ in range(random.randint(1, 4))
    ])

    case_type = factory.Faker('random_element', elements=[
        'judgment', 'order', 'interim', 'appeal', 'revision'
    ])
    relevance_score = factory.Faker('pyfloat', left_digits=0, right_digits=2, min_value=0.0, max_value=1.0)
    is_published = factory.Faker('boolean', chance_of_getting_true=80)
    view_count = factory.Faker('random_int', min=0, max=1000)

    ai_processing_status = factory.Faker('random_element', elements=[
        'pending', 'processing', 'completed', 'failed'
    ])
    ai_confidence_score = factory.Faker('pyfloat', left_digits=0, right_digits=2, min_value=0.6, max_value=0.99)
    ethical_compliance_score = factory.Faker('pyfloat', left_digits=0, right_digits=2, min_value=0.7, max_value=0.99)
    bias_detected = factory.Faker('boolean', chance_of_getting_true=10)
    human_review_required = factory.Faker('boolean', chance_of_getting_true=20)

    translated_content = factory.LazyFunction(lambda: {})
    supported_languages = factory.LazyFunction(lambda: ['en'])
    embedding_vector = factory.LazyFunction(lambda: [round(random.uniform(-1, 1), 4) for _ in range(384)])
    predicted_outcome = factory.LazyFunction(lambda: {})

    data_source = factory.Faker('random_element', elements=['manual', 'api', 'scraper', 'import'])
    source_id = factory.Sequence(lambda n: f'SRC-{n:06d}')
    source_url = factory.Faker('url')
    data_quality_score = factory.Faker('pyfloat', left_digits=0, right_digits=2, min_value=0.7, max_value=1.0)

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        """Add tags after creating case"""
        if not create:
            return

        if extracted:
            for tag in extracted:
                self.tags.add(tag)
        else:
            # Add 1-3 random tags
            num_tags = random.randint(1, 3)
            for _ in range(num_tags):
                tag = TagFactory()
                self.tags.add(tag)


class SuitFactory(DjangoModelFactory):
    """Factory for Suit model"""

    class Meta:
        model = Suit

    name = factory.LazyAttribute(lambda obj: f'{fake.random_element(["Civil", "Criminal", "Commercial", "Tax"])} Suit {fake.year()}/{fake.random_int(1, 9999)}')
    description = factory.Faker('paragraph')
    suit_type = factory.Faker('random_element', elements=[
        'civil', 'criminal', 'commercial', 'tax', 'constitutional', 'other'
    ])
    priority_level = factory.Faker('random_element', elements=[
        'low', 'medium', 'high', 'urgent'
    ])
    created_by = factory.SubFactory(UserProfileFactory)
    is_active = factory.Faker('boolean', chance_of_getting_true=80)

    @factory.post_generation
    def assigned_users(self, create, extracted, **kwargs):
        """Add assigned users after creating suit"""
        if not create:
            return

        if extracted:
            for user in extracted:
                self.assigned_users.add(user)
        else:
            # Add the creator as assigned user
            self.assigned_users.add(self.created_by)


class SearchHistoryFactory(DjangoModelFactory):
    """Factory for SearchHistory model"""

    class Meta:
        model = SearchHistory

    user = factory.SubFactory(UserFactory)
    query_text = factory.Faker('sentence', nb_words=5)
    filters = factory.LazyFunction(lambda: {
        'court': fake.random_element(['DHC', 'BHC', 'MHC', None]),
        'case_type': fake.random_element(['judgment', 'order', None]),
        'date_range': fake.random_element(['last_year', 'last_5_years', 'all', None])
    })
    results_count = factory.Faker('random_int', min=0, max=100)
    search_time = factory.Faker('pyfloat', left_digits=1, right_digits=2, min_value=0.1, max_value=5.0)


class CustomizationFactory(DjangoModelFactory):
    """Factory for Customization model"""

    class Meta:
        model = Customization
        django_get_or_create = ('user', 'suit')

    user = factory.SubFactory(UserFactory)
    suit = factory.SubFactory(SuitFactory)
    jurisdiction_emphasis = factory.LazyFunction(lambda: {
        fake.random_element(['Delhi', 'Mumbai', 'Chennai', 'Kolkata']): round(random.uniform(1.0, 2.0), 2)
        for _ in range(random.randint(1, 3))
    })
    language_preferences = factory.LazyFunction(lambda: random.sample(['en', 'hi', 'ta', 'te'], k=random.randint(1, 3)))
    precedent_statute_weight = factory.Faker('pyfloat', left_digits=0, right_digits=2, min_value=0.3, max_value=0.7)
    time_period_focus = factory.Faker('random_element', elements=[
        'recent', 'medium', 'historical', 'custom'
    ])
    analysis_focus_areas = factory.LazyFunction(lambda: random.sample([
        'contract_law', 'tort', 'damages', 'liability', 'jurisdiction', 'evidence', 'procedure'
    ], k=random.randint(2, 4)))


class UserNoteFactory(DjangoModelFactory):
    """Factory for UserNote model"""

    class Meta:
        model = UserNote
        django_get_or_create = ('user', 'case')

    user = factory.SubFactory(UserFactory)
    case = factory.SubFactory(CaseFactory)
    note_text = factory.Faker('paragraph')
    is_private = factory.Faker('boolean', chance_of_getting_true=70)
    is_starred = factory.Faker('boolean', chance_of_getting_true=30)


class SavedCaseFactory(DjangoModelFactory):
    """Factory for SavedCase model"""

    class Meta:
        model = SavedCase
        django_get_or_create = ('user', 'case')

    user = factory.SubFactory(UserFactory)
    case = factory.SubFactory(CaseFactory)
    folder = factory.Faker('random_element', elements=[
        'General', 'Important', 'Reference', 'Contract Cases', 'Criminal Cases', 'Recent'
    ])
    tags = factory.Faker('words', nb=3)


class AnalyticsDataFactory(DjangoModelFactory):
    """Factory for AnalyticsData model"""

    class Meta:
        model = AnalyticsData

    user = factory.SubFactory(UserFactory)
    analytics_type = factory.Faker('random_element', elements=[
        'search_trends', 'case_views', 'user_activity', 'system_usage', 'predictions'
    ])
    data = factory.LazyFunction(lambda: {
        'total_count': random.randint(10, 1000),
        'average': round(random.uniform(10, 100), 2),
        'trend': random.choice(['increasing', 'decreasing', 'stable']),
        'breakdown': {
            fake.word(): random.randint(1, 100)
            for _ in range(5)
        }
    })
    period_start = factory.Faker('date_between', start_date='-1y', end_date='-1m')
    period_end = factory.LazyAttribute(lambda obj: obj.period_start + timedelta(days=30))


# ============================================================================
# Batch Factories for Creating Multiple Instances
# ============================================================================

def create_sample_courts(count=10):
    """Create multiple HighCourt instances"""
    return [HighCourtFactory() for _ in range(count)]


def create_sample_users(count=5):
    """Create multiple User instances with profiles"""
    users = []
    for _ in range(count):
        user = UserFactory()
        UserProfileFactory(user=user)
        users.append(user)
    return users


def create_sample_cases(count=20, court=None, tags=None):
    """Create multiple Case instances"""
    cases = []
    for _ in range(count):
        case_kwargs = {}
        if court:
            case_kwargs['court'] = court
        if tags:
            case_kwargs['tags'] = tags
        case = CaseFactory(**case_kwargs)
        cases.append(case)
    return cases


def create_complete_test_dataset():
    """Create a complete test dataset with related instances"""
    # Create courts
    courts = create_sample_courts(5)

    # Create tags
    tags = [TagFactory() for _ in range(10)]

    # Create users with profiles
    users = create_sample_users(10)

    # Create cases
    cases = []
    for court in courts:
        cases.extend(create_sample_cases(10, court=court))

    # Create suits and assign to users
    suits = []
    for user in users[:5]:
        profile = UserProfile.objects.get(user=user)
        suit = SuitFactory(created_by=profile)
        suits.append(suit)

    # Create search history
    for user in users:
        for _ in range(random.randint(5, 15)):
            SearchHistoryFactory(user=user)

    # Create saved cases and notes
    for user in users:
        selected_cases = random.sample(cases, min(5, len(cases)))
        for case in selected_cases:
            SavedCaseFactory(user=user, case=case)
            if random.random() > 0.5:
                UserNoteFactory(user=user, case=case)

    return {
        'courts': courts,
        'tags': tags,
        'users': users,
        'cases': cases,
        'suits': suits
    }
