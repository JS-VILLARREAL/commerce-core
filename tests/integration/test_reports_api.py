import pytest


@pytest.mark.asyncio
async def test_top_products_empty(client, auth_headers):
    response = await client.get("/api/v1/reports/top-products", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_top_products_with_orders(client, auth_headers):
    # Create products
    p1 = await client.post(
        "/api/v1/products/",
        headers=auth_headers,
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
        headers=auth_headers,
        json={
            "name": "Average",
            "sku": "AVG-001",
            "price": "20.00",
            "stock": 100,
            "category": "B",
        },
    )
    pid1 = p1.json()["id"]
    pid2 = p2.json()["id"]

    # Create orders
    await client.post(
        "/api/v1/orders/",
        headers=auth_headers,
        json={
            "customer_name": "C1",
            "customer_email": "c1@test.com",
            "items": [{"product_id": pid1, "quantity": 10}],
        },
    )
    await client.post(
        "/api/v1/orders/",
        headers=auth_headers,
        json={
            "customer_name": "C2",
            "customer_email": "c2@test.com",
            "items": [{"product_id": pid2, "quantity": 3}],
        },
    )

    response = await client.get(
        "/api/v1/reports/top-products?limit=5", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["product_name"] == "Best Seller"
    assert data[0]["total_sold"] == 10


@pytest.mark.asyncio
async def test_sales_report_empty(client, auth_headers):
    response = await client.get(
        "/api/v1/reports/sales?from=2026-01-01&to=2026-01-31", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_sales_report_validation(client, auth_headers):
    response = await client.get(
        "/api/v1/reports/sales?from=invalid&to=also-invalid", headers=auth_headers
    )
    assert response.status_code == 422
