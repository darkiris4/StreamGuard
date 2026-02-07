from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_hosts_crud():
    create_payload = {
        "hostname": "host-1",
        "ip_address": "10.0.0.10",
        "ssh_user": "root",
        "os_distro": "rhel",
        "os_version": "9",
    }
    response = client.post("/api/hosts", json=create_payload)
    assert response.status_code == 200
    host_id = response.json()["id"]

    response = client.get("/api/hosts")
    assert response.status_code == 200
    assert any(item["id"] == host_id for item in response.json())

    response = client.get(f"/api/hosts/{host_id}")
    assert response.status_code == 200
    assert response.json()["hostname"] == "host-1"

    response = client.put(f"/api/hosts/{host_id}", json={"os_version": "9.3"})
    assert response.status_code == 200
    assert response.json()["os_version"] == "9.3"

    response = client.delete(f"/api/hosts/{host_id}")
    assert response.status_code == 200


def test_hosts_test_connection(monkeypatch):
    class FakeClient:
        def set_missing_host_key_policy(self, policy):
            pass

        def connect(self, **kwargs):
            return None

        def close(self):
            return None

    monkeypatch.setattr("paramiko.SSHClient", lambda: FakeClient())

    response = client.post(
        "/api/hosts/test-connection",
        json={"hostname": "localhost", "ssh_user": "root"},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
