from fastapi.testclient import TestClient

from app.database import get_db
from tests.conftest import auth_headers


class TestAuthorizationAPI:
    def test_create_diagnostico_without_token(self, client: TestClient):
        response = client.post("/api/v1/diagnosticos", json={
            "dor_migratoria": True,
            "anorexia": False,
            "nauseas_vomitos": False,
            "dor_fid": True,
            "descompressao_dolorosa": False,
            "temperatura": 36.8,
            "leucocitos": 12000,
            "neutrofilia": False,
        })
        assert response.status_code == 401

    def test_create_diagnostico_admin(self, client: TestClient, test_admin, db_session):
        headers = auth_headers(test_admin)
        response = client.post("/api/v1/diagnosticos", json={
            "dor_migratoria": True,
            "anorexia": False,
            "nauseas_vomitos": False,
            "dor_fid": True,
            "descompressao_dolorosa": False,
            "temperatura": 36.8,
            "leucocitos": 12000,
            "neutrofilia": False,
        }, headers=headers)
        assert response.status_code in (201, 503)

    def test_create_diagnostico_viewer_forbidden(self, client: TestClient, test_viewer):
        headers = auth_headers(test_viewer)
        response = client.post("/api/v1/diagnosticos", json={
            "dor_migratoria": True,
            "anorexia": False,
            "nauseas_vomitos": False,
            "dor_fid": True,
            "descompressao_dolorosa": False,
            "temperatura": 36.8,
            "leucocitos": 12000,
            "neutrofilia": False,
        }, headers=headers)
        assert response.status_code == 403

    def test_list_diagnosticos_viewer_allowed(self, client: TestClient, test_viewer):
        headers = auth_headers(test_viewer)
        response = client.get("/api/v1/diagnosticos", headers=headers)
        assert response.status_code == 200

    def test_list_diagnosticos_professional_allowed(self, client: TestClient, test_user):
        headers = auth_headers(test_user)
        response = client.get("/api/v1/diagnosticos", headers=headers)
        assert response.status_code == 200

    def test_delete_diagnostico_viewer_forbidden(self, client: TestClient, test_viewer):
        headers = auth_headers(test_viewer)
        response = client.delete("/api/v1/diagnosticos/999", headers=headers)
        assert response.status_code == 403

    def test_delete_diagnostico_admin_allowed(self, client: TestClient, test_admin):
        headers = auth_headers(test_admin)
        response = client.delete("/api/v1/diagnosticos/999", headers=headers)
        assert response.status_code == 404

    def test_metricas_viewer_allowed(self, client: TestClient, test_viewer):
        headers = auth_headers(test_viewer)
        response = client.get("/api/v1/metricas", headers=headers)
        assert response.status_code in (200, 404)

    def test_endpoint_without_auth_returns_401(self, client: TestClient):
        response = client.get("/api/v1/diagnosticos")
        assert response.status_code == 401
