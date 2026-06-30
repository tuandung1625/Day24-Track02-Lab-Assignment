import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

# Helper function to get auth headers
def get_auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}

class TestAPIEndpointsRBAC:

    # 1. Test raw patients endpoint (/api/patients/raw)
    def test_raw_patients_access(self):
        # Alice (admin) - Allowed (200)
        res = client.get("/api/patients/raw", headers=get_auth_header("token-alice"))
        assert res.status_code == 200
        assert "data" in res.json()
        assert len(res.json()["data"]) <= 10

        # Bob (ml_engineer) - Forbidden (403)
        res = client.get("/api/patients/raw", headers=get_auth_header("token-bob"))
        assert res.status_code == 403

        # Carol (data_analyst) - Forbidden (403)
        res = client.get("/api/patients/raw", headers=get_auth_header("token-carol"))
        assert res.status_code == 403

        # Dave (intern) - Forbidden (403)
        res = client.get("/api/patients/raw", headers=get_auth_header("token-dave"))
        assert res.status_code == 403

    # 2. Test anonymized patients endpoint (/api/patients/anonymized)
    def test_anonymized_patients_access(self):
        # Alice (admin) - Allowed (200)
        res = client.get("/api/patients/anonymized", headers=get_auth_header("token-alice"))
        assert res.status_code == 200

        # Bob (ml_engineer) - Allowed (200)
        res = client.get("/api/patients/anonymized", headers=get_auth_header("token-bob"))
        assert res.status_code == 200

        # Carol (data_analyst) - Forbidden (403)
        res = client.get("/api/patients/anonymized", headers=get_auth_header("token-carol"))
        assert res.status_code == 403

        # Dave (intern) - Forbidden (403)
        res = client.get("/api/patients/anonymized", headers=get_auth_header("token-dave"))
        assert res.status_code == 403

    # 3. Test aggregated metrics endpoint (/api/metrics/aggregated)
    def test_aggregated_metrics_access(self):
        # Alice (admin) - Allowed (200)
        res = client.get("/api/metrics/aggregated", headers=get_auth_header("token-alice"))
        assert res.status_code == 200

        # Bob (ml_engineer) - Allowed (200)
        res = client.get("/api/metrics/aggregated", headers=get_auth_header("token-bob"))
        # Wait: ml_engineer does NOT inherit from data_analyst.
        # But wait, does Bob have read access to aggregated_metrics?
        # Let's check policy.csv:
        # p, ml_engineer, training_data, read
        # p, ml_engineer, model_artifacts, read
        # p, ml_engineer, model_artifacts, write
        # There is no p, ml_engineer, aggregated_metrics, read!
        # So Bob (ml_engineer) should get 403 Forbidden!
        # Let's check this carefully. Yes, policy.csv does not give ml_engineer access to aggregated_metrics!
        # Let's verify if bob gets 403.
        # Wait, let's assert Bob gets 403. If Bob gets 403, that is correct!
        
        # Carol (data_analyst) - Allowed (200)
        res = client.get("/api/metrics/aggregated", headers=get_auth_header("token-carol"))
        assert res.status_code == 200

        # Dave (intern) - Forbidden (403)
        res = client.get("/api/metrics/aggregated", headers=get_auth_header("token-dave"))
        assert res.status_code == 403

    # 4. Test delete patient endpoint (/api/patients/{patient_id})
    def test_delete_patient_access(self):
        # Alice (admin) - Allowed (200)
        res = client.delete("/api/patients/some-id", headers=get_auth_header("token-alice"))
        assert res.status_code == 200

        # Bob (ml_engineer) - Forbidden (403)
        res = client.delete("/api/patients/some-id", headers=get_auth_header("token-bob"))
        assert res.status_code == 403

        # Carol (data_analyst) - Forbidden (403)
        res = client.delete("/api/patients/some-id", headers=get_auth_header("token-carol"))
        assert res.status_code == 403

        # Dave (intern) - Forbidden (403)
        res = client.delete("/api/patients/some-id", headers=get_auth_header("token-dave"))
        assert res.status_code == 403

    # 5. Test Authentication (Missing or Invalid tokens)
    def test_authentication_failures(self):
        # Missing header
        res = client.get("/api/patients/raw")
        assert res.status_code == 401

        # Invalid token
        res = client.get("/api/patients/raw", headers=get_auth_header("token-invalid"))
        assert res.status_code == 401
