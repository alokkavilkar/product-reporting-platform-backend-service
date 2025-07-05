import pytest
from inspection.models import Product

@pytest.mark.django_db
def test_get_product_list(api_client, sample_product):
    sample_product(name="Widget", type="Hardware")
    response = api_client.get("/api/products/")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Widget"

@pytest.mark.django_db
def test_post_product(api_client):
    payload = {
        "name": "Gear",
        "type": "Mechanical",
        "created_by": "worker2"
    }
    response = api_client.post("/api/products/", data=payload, content_type='application/json')
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Gear"
    assert Product.objects.count() == 1

@pytest.mark.django_db
def test_post_product_invalid_payload(api_client):
    # missing 'name' and 'type'
    response = api_client.post("/api/products/", data={}, content_type='application/json')
    
    assert response.status_code == 400
