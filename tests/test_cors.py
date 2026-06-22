from fastapi.testclient import TestClient


class TestCors:
    def test_preflight_allowed_origin(self, client: TestClient):
        response = client.options(
            "/api/v1/diagnosticos",
            headers={
                "Origin": "http://localhost:8082",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:8082"
        assert "POST" in response.headers.get("access-control-allow-methods", "")

    def test_preflight_blocked_origin(self, client: TestClient):
        response = client.options(
            "/api/v1/diagnosticos",
            headers={
                "Origin": "https://evil.com",
                "Access-Control-Request-Method": "POST",
            },
        )
        cors_header = response.headers.get("access-control-allow-origin", "")
        assert "evil.com" not in cors_header

    def test_cors_headers_on_get(self, client: TestClient):
        response = client.get("/health", headers={"Origin": "http://localhost:8082"})
        assert response.headers.get("access-control-allow-origin") == "http://localhost:8082"

    def test_cors_allow_credentials(self, client: TestClient):
        response = client.options(
            "/api/v1/diagnosticos",
            headers={
                "Origin": "http://localhost:8082",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-credentials") == "true"

    def test_security_headers_present(self, client: TestClient):
        response = client.get("/health")
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"
        assert response.headers.get("strict-transport-security") is not None
