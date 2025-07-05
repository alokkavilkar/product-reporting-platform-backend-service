import pytest
from django.urls import reverse
from inspection.models import Product, Inspection

@pytest.mark.django_db
def test_inspect_product_success(api_client):
    # Create a product
    product = Product.objects.create(
        name="Widget",
        type="Hardware",
        status="pending",
        created_by="worker1"
    )

    payload = {
        "inspected_by": "inspector1",
        "result": "pass",
        "inspection_notes": "Looks good"
    }

    url = f"/api/products/{product.id}/inspect/"

    # Inject token with worker role (mocked in test mode)
    response = api_client.post(
        url,
        data=payload,
        format="json",
        HTTP_AUTHORIZATION="Bearer test-token"
    )

    assert response.status_code == 201
    data = response.json()
    assert data["product_id"] == product.id
    assert data["result"] == "pass"
    assert data["product_status"] == "inspected"

    product.refresh_from_db()
    assert product.status == "inspected"

    inspection = Inspection.objects.get(product=product)
    assert inspection.notes == "Looks good"

@pytest.mark.django_db
def test_inspect_product_invalid_payload(api_client):
    product = Product.objects.create(
        name="Widget",
        type="Hardware",
        status="pending",
        created_by="worker1"
    )

    url = f"/api/products/{product.id}/inspect/"
    response = api_client.post(
        url,
        data={},  # Missing required "result"
        format="json",
        HTTP_AUTHORIZATION="Bearer test-token"
    )

    assert response.status_code == 400
    assert "Invalid request payload" in response.content.decode()

@pytest.mark.django_db
def test_inspect_product_not_found(api_client):
    url = "/api/products/9999/inspect/"
    response = api_client.post(
        url,
        data={"result": "pass"},
        format="json",
        HTTP_AUTHORIZATION="Bearer test-token"
    )

    assert response.status_code == 404
    assert "Product not found" in response.content.decode()
