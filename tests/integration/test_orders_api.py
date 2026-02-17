import pytest


@pytest.mark.asyncio
async def test_create_order_success(client):
    # Arrange: crear producto
    p = await client.post(
        "/api/v1/products/",
        json={"name": "Widget", "sku": "WDG-001", "price": "15.50", "stock": 100},
    )
    pid = p.json()["id"]

    # Act: crear orden
    response = await client.post(
        "/api/v1/orders/",
        json={
            "customer_name": "Jane",
            "customer_email": "jane@test.com",
            "items": [{"product_id": pid, "quantity": 3}],
        },
    )

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "PENDING"
    assert float(data["total_amount"]) == 46.50
    assert len(data["items"]) == 1

    # Assert: stock decremented
    products = (await client.get("/api/v1/products/")).json()["items"]
    widget = next(p for p in products if p["sku"] == "WDG-001")
    assert widget["stock"] == 97


@pytest.mark.asyncio
async def test_create_order_insufficient_stock(client):
    p = await client.post(
        "/api/v1/products/",
        json={"name": "Rare", "sku": "RARE-001", "price": "100.00", "stock": 2},
    )
    pid = p.json()["id"]

    response = await client.post(
        "/api/v1/orders/",
        json={
            "customer_name": "John",
            "customer_email": "john@test.com",
            "items": [{"product_id": pid, "quantity": 10}],
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_order_product_not_found(client):
    response = await client.post(
        "/api/v1/orders/",
        json={
            "customer_name": "John",
            "customer_email": "john@test.com",
            "items": [{"product_id": 99999, "quantity": 1}],
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_order_by_id(client):
    p = await client.post(
        "/api/v1/products/",
        json={"name": "Gadget", "sku": "GDG-001", "price": "25.00", "stock": 50},
    )
    pid = p.json()["id"]

    order = await client.post(
        "/api/v1/orders/",
        json={
            "customer_name": "Alice",
            "customer_email": "alice@test.com",
            "items": [{"product_id": pid, "quantity": 2}],
        },
    )
    oid = order.json()["id"]

    response = await client.get(f"/api/v1/orders/{oid}")
    assert response.status_code == 200
    assert response.json()["customer_name"] == "Alice"


@pytest.mark.asyncio
async def test_get_order_not_found(client):
    response = await client.get("/api/v1/orders/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_order_validation_error(client):
    response = await client.post(
        "/api/v1/orders/",
        json={"customer_name": "", "customer_email": "not-email", "items": []},
    )
    assert response.status_code == 422
