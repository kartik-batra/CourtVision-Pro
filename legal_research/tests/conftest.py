"""
Global pytest fixtures and configuration for CourtVision-Pro tests.
"""
import os
import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.conf import settings
from unittest.mock import Mock, patch, MagicMock
import fakeredis
import numpy as np

# Set TEST_MODE environment variable for mocking control
os.environ.setdefault('TEST_MODE', 'mock')


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope='function')
def db_with_migrations(db):
    """Database fixture that includes migrations"""
    return db


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Override default database setup for test database configuration"""
    # Use in-memory SQLite for speed
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'ATOMIC_REQUESTS': True,
    }


# ============================================================================
# User and Authentication Fixtures
# ============================================================================

@pytest.fixture
def test_user(db):
    """Create a test user"""
    user = User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )
    return user


@pytest.fixture
def test_user_with_profile(test_user, test_high_court):
    """Create a test user with UserProfile"""
    from legal_research.models import UserProfile

    profile = UserProfile.objects.create(
        user=test_user,
        high_court=test_high_court,
        designation='Judge',
        employee_id='EMP001',
        phone_number='+91-9876543210',
        default_language='en',
        notification_settings={'email': True, 'sms': False},
        preferences={'theme': 'light', 'results_per_page': 20}
    )
    return test_user


@pytest.fixture
def admin_user(db):
    """Create an admin user"""
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )
    return admin


@pytest.fixture
def authenticated_client(test_user):
    """Create an authenticated Django test client"""
    client = Client()
    client.force_login(test_user)
    return client


@pytest.fixture
def admin_client(admin_user):
    """Create an authenticated admin Django test client"""
    client = Client()
    client.force_login(admin_user)
    return client


# ============================================================================
# Model Instance Fixtures
# ============================================================================

@pytest.fixture
def test_high_court(db):
    """Create a test HighCourt instance"""
    from legal_research.models import HighCourt
    from datetime import date

    court = HighCourt.objects.create(
        name='Delhi High Court',
        jurisdiction='Delhi',
        code='DHC',
        established_date=date(1966, 10, 31),
        is_active=True
    )
    return court


@pytest.fixture
def test_tag(db):
    """Create a test Tag instance"""
    from legal_research.models import Tag

    tag = Tag.objects.create(
        name='Contract Law',
        description='Cases related to contract law',
        color='#FF5733'
    )
    return tag


@pytest.fixture
def test_case(db, test_high_court, test_tag):
    """Create a test Case instance"""
    from legal_research.models import Case
    from datetime import date

    case = Case.objects.create(
        title='Test Case vs Union of India',
        citation='2024 DHC 001',
        court=test_high_court,
        bench='Division Bench',
        judgment_date=date(2024, 1, 15),
        decision_date=date(2024, 1, 20),
        petitioners='John Doe, Jane Doe',
        respondents='Union of India, State of Delhi',
        case_text='This is a test case with detailed judgment text...',
        headnotes='Brief summary of the case',
        case_type='judgment',
        is_published=True,
        relevance_score=0.85,
        ai_processing_status='completed',
        ai_confidence_score=0.9,
        ethical_compliance_score=0.95
    )
    case.tags.add(test_tag)
    return case


@pytest.fixture
def test_suit(db, test_user_with_profile):
    """Create a test Suit instance"""
    from legal_research.models import Suit, UserProfile

    profile = UserProfile.objects.get(user=test_user_with_profile)
    suit = Suit.objects.create(
        name='Civil Suit 2024',
        description='Test civil suit',
        suit_type='civil',
        priority_level='high',
        created_by=profile,
        is_active=True
    )
    suit.assigned_users.add(profile)
    return suit


@pytest.fixture
def test_search_history(db, test_user):
    """Create a test SearchHistory instance"""
    from legal_research.models import SearchHistory

    search = SearchHistory.objects.create(
        user=test_user,
        query_text='contract breach damages',
        filters={'court': 'DHC', 'date_range': 'last_year'},
        results_count=15,
        search_time=0.45
    )
    return search


@pytest.fixture
def test_customization(db, test_user, test_suit):
    """Create a test Customization instance"""
    from legal_research.models import Customization

    customization = Customization.objects.create(
        user=test_user,
        suit=test_suit,
        jurisdiction_emphasis={'Delhi': 1.5, 'Punjab': 1.2},
        language_preferences=['en', 'hi'],
        precedent_statute_weight=0.6,
        time_period_focus='recent',
        analysis_focus_areas=['contract_law', 'damages', 'liability']
    )
    return customization


@pytest.fixture
def test_user_note(db, test_user, test_case):
    """Create a test UserNote instance"""
    from legal_research.models import UserNote

    note = UserNote.objects.create(
        user=test_user,
        case=test_case,
        note_text='Important case for contract disputes',
        is_private=True,
        is_starred=True
    )
    return note


@pytest.fixture
def test_saved_case(db, test_user, test_case):
    """Create a test SavedCase instance"""
    from legal_research.models import SavedCase

    saved = SavedCase.objects.create(
        user=test_user,
        case=test_case,
        folder='Contract Cases',
        tags='important, reference'
    )
    return saved


@pytest.fixture
def multiple_cases(db, test_high_court, test_tag):
    """Create multiple test cases for search/filter testing"""
    from legal_research.models import Case
    from datetime import date, timedelta

    cases = []
    for i in range(10):
        case = Case.objects.create(
            title=f'Test Case {i+1} vs Respondent',
            citation=f'2024 DHC {i+1:03d}',
            court=test_high_court,
            judgment_date=date(2024, 1, 1) + timedelta(days=i*10),
            decision_date=date(2024, 1, 5) + timedelta(days=i*10),
            petitioners=f'Petitioner {i+1}',
            respondents=f'Respondent {i+1}',
            case_text=f'This is test case {i+1} with detailed content...',
            headnotes=f'Headnotes for case {i+1}',
            case_type='judgment',
            is_published=True,
            relevance_score=0.5 + (i * 0.05)
        )
        case.tags.add(test_tag)
        cases.append(case)

    return cases


# ============================================================================
# External Service Mocking Fixtures
# ============================================================================

@pytest.fixture
def mock_redis():
    """Mock Redis cache using fakeredis"""
    fake_redis = fakeredis.FakeRedis()
    with patch('django.core.cache.cache', fake_redis):
        yield fake_redis


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI API client"""
    mock_client = MagicMock()

    # Mock chat completions
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content='{"summary": "Test summary", "key_points": ["Point 1", "Point 2"]}'))
    ]
    mock_client.chat.completions.create.return_value = mock_completion

    # Mock embeddings
    mock_embedding = MagicMock()
    mock_embedding.data = [MagicMock(embedding=[0.1] * 384)]
    mock_client.embeddings.create.return_value = mock_embedding

    return mock_client


@pytest.fixture
def mock_elasticsearch():
    """Mock Elasticsearch client"""
    mock_es = MagicMock()

    # Mock ping
    mock_es.ping.return_value = True

    # Mock search results
    mock_es.search.return_value = {
        'hits': {
            'total': {'value': 10},
            'hits': [
                {
                    '_id': f'case-{i}',
                    '_score': 0.9 - (i * 0.05),
                    '_source': {
                        'title': f'Test Case {i}',
                        'citation': f'2024 DHC {i:03d}'
                    }
                }
                for i in range(5)
            ]
        }
    }

    # Mock bulk operations
    mock_es.bulk.return_value = {'errors': False}

    # Mock index operations
    mock_es.indices.exists.return_value = False
    mock_es.indices.create.return_value = {'acknowledged': True}

    return mock_es


@pytest.fixture
def mock_faiss_index():
    """Mock FAISS vector index"""
    mock_index = MagicMock()

    # Mock search results
    def mock_search(vectors, k):
        # Return fake distances and indices
        distances = np.array([[0.95 - (i * 0.05) for i in range(k)]])
        indices = np.array([[i for i in range(k)]])
        return distances, indices

    mock_index.search = mock_search
    mock_index.add = MagicMock()
    mock_index.ntotal = 100

    return mock_index


@pytest.fixture
def mock_sentence_transformer():
    """Mock SentenceTransformer model"""
    mock_model = MagicMock()

    # Mock encode method to return fake embeddings
    def mock_encode(texts, **kwargs):
        if isinstance(texts, str):
            return np.random.rand(384)
        return np.random.rand(len(texts), 384)

    mock_model.encode = mock_encode

    return mock_model


@pytest.fixture
def mock_spacy_nlp():
    """Mock spaCy NLP model"""
    mock_nlp = MagicMock()

    # Mock document processing
    mock_doc = MagicMock()
    mock_doc.ents = [
        MagicMock(text='John Doe', label_='PERSON', start=0, end=8),
        MagicMock(text='Delhi High Court', label_='ORG', start=20, end=36),
        MagicMock(text='2024', label_='DATE', start=50, end=54),
    ]

    mock_nlp.return_value = mock_doc

    return mock_nlp


@pytest.fixture
def mock_transformers():
    """Mock Hugging Face transformers"""
    mock_tokenizer = MagicMock()
    mock_tokenizer.return_value = {
        'input_ids': [[1, 2, 3, 4]],
        'attention_mask': [[1, 1, 1, 1]]
    }

    mock_model = MagicMock()
    mock_output = MagicMock()
    mock_output.last_hidden_state = np.random.rand(1, 4, 384)
    mock_model.return_value = mock_output

    return mock_tokenizer, mock_model


@pytest.fixture
def mock_celery_task():
    """Mock Celery task execution (eager mode)"""
    with patch('celery.app.task.Task.apply_async') as mock_apply:
        mock_result = MagicMock()
        mock_result.id = 'test-task-id-123'
        mock_result.ready.return_value = True
        mock_result.get.return_value = {'status': 'success'}
        mock_apply.return_value = mock_result
        yield mock_apply


# ============================================================================
# AI Service Mocking Fixtures
# ============================================================================

@pytest.fixture
def mock_ai_services(mock_openai_client, mock_sentence_transformer, mock_spacy_nlp):
    """Mock all AI services together"""
    with patch('legal_research.ai_integration.OpenAIClient') as mock_openai_class, \
         patch('sentence_transformers.SentenceTransformer') as mock_st_class, \
         patch('spacy.load') as mock_spacy_load:

        mock_openai_class.return_value = mock_openai_client
        mock_st_class.return_value = mock_sentence_transformer
        mock_spacy_load.return_value = mock_spacy_nlp

        yield {
            'openai': mock_openai_client,
            'sentence_transformer': mock_sentence_transformer,
            'spacy': mock_spacy_nlp
        }


@pytest.fixture
def mock_search_engine(mock_elasticsearch, mock_faiss_index, mock_sentence_transformer):
    """Mock search engine components"""
    with patch('elasticsearch.Elasticsearch') as mock_es_class, \
         patch('faiss.IndexFlatIP') as mock_faiss_class, \
         patch('sentence_transformers.SentenceTransformer') as mock_st_class:

        mock_es_class.return_value = mock_elasticsearch
        mock_faiss_class.return_value = mock_faiss_index
        mock_st_class.return_value = mock_sentence_transformer

        yield {
            'elasticsearch': mock_elasticsearch,
            'faiss': mock_faiss_index,
            'model': mock_sentence_transformer
        }


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_legal_text():
    """Sample legal case text for testing"""
    return """
    In the matter of John Doe vs Union of India, the Delhi High Court examined
    the question of breach of contract under Section 73 of the Indian Contract Act, 1872.

    The petitioner alleged that the respondent failed to deliver goods as per the agreement
    dated January 15, 2023. The court noted that the essential elements of breach were
    satisfied in this case.

    After careful consideration of precedents including Hadley v Baxendale and
    Indian Oil Corporation v NEPC, the court held that the petitioner was entitled
    to damages amounting to Rs. 10,00,000.

    The decision was rendered on March 20, 2024, by Justice A.K. Sharma and
    Justice B.C. Verma (Division Bench).
    """


@pytest.fixture
def sample_ai_summary():
    """Sample AI-generated summary for testing"""
    return {
        'summary': 'Case involving breach of contract and damages',
        'key_points': [
            'Breach of contract under Indian Contract Act',
            'Failure to deliver goods as per agreement',
            'Damages awarded to petitioner'
        ],
        'decision': 'Petitioner awarded damages of Rs. 10,00,000',
        'implications': 'Reinforces strict liability for contractual breaches',
        'statutes_cited': ['Indian Contract Act, 1872 - Section 73'],
        'precedents_cited': [
            'Hadley v Baxendale',
            'Indian Oil Corporation v NEPC'
        ]
    }


@pytest.fixture
def sample_search_filters():
    """Sample search filters for testing"""
    return {
        'court': 'DHC',
        'case_type': 'judgment',
        'date_start': '2023-01-01',
        'date_end': '2024-12-31',
        'tags': ['contract_law', 'damages']
    }


@pytest.fixture
def sample_case_features():
    """Sample case features for ML testing"""
    return {
        'case_type': 'civil',
        'court': 'Delhi High Court',
        'year': 2024,
        'tags': ['contract', 'breach', 'damages'],
        'complexity_score': 0.75,
        'precedent_count': 5,
        'statute_count': 3,
        'text_length': 5000
    }


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def capture_logs(caplog):
    """Capture log messages during tests"""
    import logging
    caplog.set_level(logging.INFO)
    return caplog


@pytest.fixture
def temp_media_root(tmp_path, settings):
    """Temporary media root for file upload tests"""
    temp_media = tmp_path / "media"
    temp_media.mkdir()
    settings.MEDIA_ROOT = temp_media
    return temp_media


@pytest.fixture
def sample_uploaded_file():
    """Create a sample uploaded file for testing"""
    from django.core.files.uploadedfile import SimpleUploadedFile

    content = b"Sample case document content for testing..."
    return SimpleUploadedFile("test_case.txt", content, content_type="text/plain")


# ============================================================================
# Test Mode Configuration
# ============================================================================

@pytest.fixture(scope='session', autouse=True)
def configure_test_mode():
    """Configure test mode for all tests"""
    # Set environment variables for testing
    os.environ['TEST_MODE'] = 'mock'
    os.environ['DJANGO_SETTINGS_MODULE'] = 'courtvision.settings'

    # Disable Celery task execution (use eager mode)
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True

    # Use fake Redis for caching
    settings.CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

    # Disable external API calls
    settings.AI_SETTINGS['OPENAI_API_KEY'] = 'test-key-mock'
    settings.AI_SETTINGS['ELASTICSEARCH_HOST'] = 'localhost:9999'  # Non-existent

    yield

    # Cleanup after tests
    os.environ.pop('TEST_MODE', None)


@pytest.fixture
def enable_integration_mode():
    """Enable integration test mode with real services (where available)"""
    original_mode = os.environ.get('TEST_MODE')
    os.environ['TEST_MODE'] = 'integration'

    yield

    if original_mode:
        os.environ['TEST_MODE'] = original_mode
    else:
        os.environ.pop('TEST_MODE', None)
