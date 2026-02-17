import pytest


@pytest.mark.asyncio
async def test_create_product(client):
    response = await client.post(
        "/api/v1/products/",
        json={
            "name": "Laptop Pro",
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
    assert "id" in data


@pytest.mark.asyncio
async def test_create_product_validation_error(client):
    response = await client.post(
        "/api/v1/products/",
        json={"name": "", "sku": "", "price": -10, "stock": -1},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_products_empty(client):
    response = await client.get("/api/v1/products/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_products_pagination(client):
    for i in range(5):
        await client.post(
            "/api/v1/products/",
            json={"name": f"P{i}", "sku": f"PG-{i}", "price": "10.00", "stock": 1},
        )

    response = await client.get("/api/v1/products/?page=1&page_size=2")
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["total_pages"] == 3
