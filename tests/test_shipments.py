def create_shipment(client):
    return client.post(
        "/shipments",
        json={"recipient": "Sample Customer", "destination": "Manchester, UK"},
    )


def test_create_and_get_shipment(client):
    created = create_shipment(client)

    assert created.status_code == 201
    shipment = created.json()
    assert shipment["tracking_number"].startswith("PKG-")
    assert shipment["status"] == "created"

    fetched = client.get(f"/shipments/{shipment['tracking_number']}")
    assert fetched.status_code == 200
    assert fetched.json() == shipment


def test_list_shipments(client):
    create_shipment(client)

    response = client.get("/shipments")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["recipient"] == "Sample Customer"


def test_update_shipment_status(client):
    shipment = create_shipment(client).json()

    response = client.patch(
        f"/shipments/{shipment['tracking_number']}/status",
        json={"status": "in_transit"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "in_transit"


def test_unknown_shipment_returns_404(client):
    response = client.get("/shipments/PKG-DOESNOTEXIST")

    assert response.status_code == 404
    assert response.json() == {"detail": "shipment not found"}


def test_invalid_status_returns_422(client):
    shipment = create_shipment(client).json()

    response = client.patch(
        f"/shipments/{shipment['tracking_number']}/status",
        json={"status": "teleported"},
    )

    assert response.status_code == 422
