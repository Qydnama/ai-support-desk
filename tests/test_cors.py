from fastapi.testclient import TestClient


def test_spa_preflight_allows_authorization_header(
    client: TestClient,
) -> None:
    response = client.options(
        "/auth/me",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == (
        "http://localhost:3000"
    )
    assert response.headers["Access-Control-Allow-Credentials"] == (
        "true"
    )
    assert "authorization" in response.headers[
        "Access-Control-Allow-Headers"
    ].lower()
