from app.core.security import hash_password
from app.models.user import User, UserRole, UserStatus


def _create_admin(db) -> User:
    admin = User(
        email="admin@example.com",
        password_hash=hash_password("supersecret"),
        name="Admin",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
    )
    db.add(admin)
    db.commit()
    return admin


def _login(client, email: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": "supersecret"})
    return response.json()["access_token"]


def test_admin_can_create_market_asset_tier_and_signal_with_targets(client, db):
    admin = _create_admin(db)
    headers = {"Authorization": f"Bearer {_login(client, admin.email)}"}

    market_resp = client.post(
        "/admin/markets", json={"code": "crypto", "name_i18n_key": "markets.crypto.name"}, headers=headers
    )
    assert market_resp.status_code == 201
    market_id = market_resp.json()["id"]

    asset_resp = client.post(
        "/admin/assets",
        json={"market_id": market_id, "symbol": "BTCUSDT", "display_name": "BTC/USDT"},
        headers=headers,
    )
    assert asset_resp.status_code == 201
    asset_id = asset_resp.json()["id"]

    tier_resp = client.post(
        "/admin/subscription-tiers",
        json={
            "code": "pro",
            "name_i18n_key": "tiers.pro.name",
            "price_cents": 5000,
            "billing_interval": "monthly",
            "markets_allowed": ["crypto"],
        },
        headers=headers,
    )
    assert tier_resp.status_code == 201

    signal_resp = client.post(
        "/admin/signals",
        json={
            "asset_id": asset_id,
            "direction": "buy",
            "entry_price": "100.00",
            "stop_loss": "90.00",
            "timeframe": "H1",
            "confidence_level": "high",
            "source": "manual",
            "visibility_tier": "pro",
            "targets": [{"order": 1, "target_price": "110.00"}, {"order": 2, "target_price": "120.00"}],
        },
        headers=headers,
    )
    assert signal_resp.status_code == 201
    body = signal_resp.json()
    assert body["status"] == "pending"
    assert body["created_by_admin_id"] is not None
    assert len(body["targets"]) == 2

    signal_id = body["id"]
    update_resp = client.put(
        f"/admin/signals/{signal_id}",
        json={"status": "active", "published_at": "2026-07-20T12:00:00Z"},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "active"

    list_resp = client.get("/admin/signals", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


def test_signal_create_requires_algorithm_name_when_source_is_algorithm(client, db):
    admin = _create_admin(db)
    headers = {"Authorization": f"Bearer {_login(client, admin.email)}"}

    market_resp = client.post(
        "/admin/markets", json={"code": "crypto", "name_i18n_key": "markets.crypto.name"}, headers=headers
    )
    asset_resp = client.post(
        "/admin/assets",
        json={"market_id": market_resp.json()["id"], "symbol": "BTCUSDT", "display_name": "BTC/USDT"},
        headers=headers,
    )

    response = client.post(
        "/admin/signals",
        json={
            "asset_id": asset_resp.json()["id"],
            "direction": "buy",
            "entry_price": "100.00",
            "stop_loss": "90.00",
            "timeframe": "H1",
            "confidence_level": "high",
            "source": "algorithm",
            "visibility_tier": "pro",
            "targets": [{"order": 1, "target_price": "110.00"}],
        },
        headers=headers,
    )
    assert response.status_code == 422


def test_subscriber_cannot_access_admin_routes(client, db):
    subscriber = User(
        email="sub2@example.com",
        password_hash=hash_password("supersecret"),
        name="Sub",
        role=UserRole.SUBSCRIBER,
        status=UserStatus.ACTIVE,
    )
    db.add(subscriber)
    db.commit()

    token = _login(client, subscriber.email)
    response = client.get("/admin/signals", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
