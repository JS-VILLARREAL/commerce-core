import pytest


@pytest.mark.asyncio
async def test_create_order_success(client, auth_headers):
    # Create a product first
    product_resp = await client.post(
        "/api/v1/products/",
        headers=auth_headers,
        json={"name": "Widget", "sku": "WDG-001", "price": "15.50", "stock": 100},
    )
    product_id = product_resp.json()["id"]

    # Create order
    response = await client.post(
        "/api/v1/orders/",
        headers=auth_headers,
        json={
            "customer_name": "Jane Doe",
            "customer_email": "jane@example.com",
            "items": [{"product_id": product_id, "quantity": 3}],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["customer_name"] == "Jane Doe"
    assert data["status"] == "PENDING"
    assert float(data["total_amount"]) == 46.50
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 3

    # Verify stock was decremented
    products_resp = await client.get("/api/v1/products/", headers=auth_headers)
    products = products_resp.json()["items"]
    widget = next(p for p in products if p["sku"] == "WDG-001")
    assert widget["stock"] == 97


@pytest.mark.asyncio
async def test_create_order_insufficient_stock(client, auth_headers):
    product_resp = await client.post(
        "/api/v1/products/",
        headers=auth_headers,
        json={"name": "Rare Item", "sku": "RARE-001", "price": "100.00", "stock": 2},
    )
    product_id = product_resp.json()["id"]

    response = await client.post(
        "/api/v1/orders/",
        headers=auth_headers,
        json={
            "customer_name": "John",
            "customer_email": "john@example.com",
            "items": [{"product_id": product_id, "quantity": 10}],
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_order_product_not_found(client, auth_headers):
    response = await client.post(
        "/api/v1/orders/",
        headers=auth_headers,
        json={
            "customer_name": "John",
            "customer_email": "john@example.com",
            "items": [{"product_id": 99999, "quantity": 1}],
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_order_by_id(client, auth_headers):
    # Create product and order
    product_resp = await client.post(
        "/api/v1/products/",
        headers=auth_headers,
        json={"name": "Gadget", "sku": "GDG-001", "price": "25.00", "stock": 50},
    )
    product_id = product_resp.json()["id"]

    order_resp = await client.post(
        "/api/v1/orders/",
        headers=auth_headers,
        json={
            "customer_name": "Alice",
            "customer_email": "alice@example.com",
            "items": [{"product_id": product_id, "quantity": 2}],
        },
    )
    order_id = order_resp.json()["id"]

    # Get order
    response = await client.get(f"/api/v1/orders/{order_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == order_id
    assert data["customer_name"] == "Alice"


@pytest.mark.asyncio
async def test_get_order_not_found(client, auth_headers):
    response = await client.get("/api/v1/orders/99999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_order_validation_error(client, auth_headers):
    response = await client.post(
        "/api/v1/orders/",
        headers=auth_headers,
        json={
            "customer_name": "",
            "customer_email": "not-an-email",
            "items": [],
        },
    )
    assert response.status_code == 422
