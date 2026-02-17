import pytest


@pytest.mark.asyncio
async def test_top_products_empty(client):
    response = await client.get("/api/v1/reports/top-products")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_top_products_with_orders(client):
    p1 = await client.post(
        "/api/v1/products/",
        json={
            "name": "Best Seller",
            "sku": "BS-001",
            "price": "10.00",
            "stock": 100,
            "category": "A",
        },
    )
    p2 = await client.post(
        "/api/v1/products/",
        json={
            "name": "Average",
            "sku": "AVG-001",
            "price": "20.00",
            "stock": 100,
            "category": "B",
        },
    )

    await client.post(
        "/api/v1/orders/",
        json={
            "customer_name": "C1",
            "customer_email": "c1@test.com",
            "items": [{"product_id": p1.json()["id"], "quantity": 10}],
        },
    )
    await client.post(
        "/api/v1/orders/",
        json={
            "customer_name": "C2",
            "customer_email": "c2@test.com",
            "items": [{"product_id": p2.json()["id"], "quantity": 3}],
        },
    )

    response = await client.get("/api/v1/reports/top-products?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["product_name"] == "Best Seller"
    assert data[0]["total_sold"] == 10


@pytest.mark.asyncio
async def test_sales_report_empty(client):
    response = await client.get("/api/v1/reports/sales?from=2026-01-01&to=2026-01-31")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_sales_report_validation(client):
    response = await client.get("/api/v1/reports/sales?from=invalid&to=also-invalid")
    assert response.status_code == 422
