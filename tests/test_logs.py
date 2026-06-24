"""Testes do endpoint de logs e do registro de execucoes/erros."""

import os

os.environ.setdefault("ADMIN_PASSWORD", "admin123")

from fastapi.testclient import TestClient

from app.main import app


def _login_admin(client):
    r = client.post(
        "/auth/login", json={"username": "admin", "password": "admin123"}
    )
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_logs_exige_autenticacao():
    with TestClient(app) as client:
        r = client.get("/api/v1/logs")
        assert r.status_code == 401


def test_logs_admin_retorna_execucoes():
    with TestClient(app) as client:
        headers = _login_admin(client)
        # gera atividade
        client.get("/health")
        r = client.get("/api/v1/logs?limite=50", headers=headers)
        assert r.status_code == 200
        body = r.json()
        assert "logs" in body and "total" in body
        # deve haver ao menos uma linha registrada
        assert body["total"] >= 1
        # o registro de login bem-sucedido deve aparecer
        mensagens = [linha["mensagem"] for linha in body["logs"]]
        assert any("Login bem-sucedido" in m for m in mensagens)


def test_logs_filtro_por_nivel():
    with TestClient(app) as client:
        headers = _login_admin(client)
        # provoca um WARNING (login falho) e um 401
        client.post(
            "/auth/login", json={"username": "admin", "password": "errada"}
        )
        client.get("/api/v1/logs")  # sem token -> 401 (WARNING)
        r = client.get("/api/v1/logs?nivel=WARNING&limite=50", headers=headers)
        assert r.status_code == 200
        for linha in r.json()["logs"]:
            assert linha["nivel"] == "WARNING"


def test_logs_nao_vaza_senha():
    with TestClient(app) as client:
        headers = _login_admin(client)
        client.post(
            "/auth/login", json={"username": "admin", "password": "segredo123"}
        )
        r = client.get("/api/v1/logs?limite=100", headers=headers)
        texto = " ".join(linha["mensagem"] for linha in r.json()["logs"])
        assert "segredo123" not in texto
