# conftest.py
import pytest
from rest_framework.test import APIClient
from inspection.models import Product

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def sample_product():
    def _create(name="Test Product", type="Sample", created_by="worker1"):
        return Product.objects.create(name=name, type=type, created_by=created_by)
    return _create
