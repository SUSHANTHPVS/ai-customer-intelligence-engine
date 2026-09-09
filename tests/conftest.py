"""
Pytest configuration and fixtures
"""
import pytest
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
pytest.ini_path = PROJECT_ROOT


@pytest.fixture
def sample_customer_data():
    """Sample customer data for testing"""
    return {
        'customer_id': 'C000001',
        'email': 'test@example.com',
        'signup_date': '2024-01-01',
        'country': 'USA',
        'industry': 'SaaS',
    }


@pytest.fixture
def sample_events_data():
    """Sample events data for testing"""
    return [
        {
            'event_id': 'E000001',
            'customer_id': 'C000001',
            'event_type': 'login',
            'event_timestamp': '2024-01-15 10:30:00',
        },
        {
            'event_id': 'E000002',
            'customer_id': 'C000001',
            'event_type': 'feature_usage',
            'event_timestamp': '2024-01-15 10:45:00',
        },
    ]
