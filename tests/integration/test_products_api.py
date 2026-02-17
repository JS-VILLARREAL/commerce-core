import pytest


@pytest.mark.asyncio
async def test_create_product(client, auth_headers):
    response = await client.post(
        "/api/v1/products/",
        headers=auth_headers,
        json={
            "name": "Laptop Pro",
            "description": "High-end laptop",
            "sku": "LAP-001",
            "price": "999.99",
            "stock": 50,
            "category": "Electronics",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Laptop Pro"
    assert data["sku"] == "LAP-001"
    assert data["stock"] == 50
    assert "id" in data


@pytest.mark.asyncio
async def test_create_product_validation_error(client, auth_headers):
    response = await client.post(
        "/api/v1/products/",
        headers=auth_headers,
        json={"name": "", "sku": "", "price": -10, "stock": -1},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_products_empty(client, auth_headers):
    response = await client.get("/api/v1/products/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_products_with_data(client, auth_headers):
    # Create two products
    await client.post(
        "/api/v1/products/",
        headers=auth_headers,
        json={"name": "P1", "sku": "SKU-1", "price": "10.00", "stock": 5},
    )
    await client.post(
        "/api/v1/products/",
        headers=auth_headers,
        json={"name": "P2", "sku": "SKU-2", "price": "20.00", "stock": 10},
    )

    response = await client.get(
        "/api/v1/products/?page=1&page_size=10", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_list_products_pagination(client, auth_headers):
    for i in range(5):
        await client.post(
            "/api/v1/products/",
            headers=auth_headers,
            json={"name": f"P{i}", "sku": f"PG-{i}", "price": "10.00", "stock": 1},
        )

    response = await client.get(
        "/api/v1/products/?page=1&page_size=2", headers=auth_headers
    )
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["total_pages"] == 3
