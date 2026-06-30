import pytest
import subprocess
import json
import os

# Append the custom OPA path so that the test can find the opa executable
os.environ["PATH"] += ";C:\\Users\\thuan\\.git-secrets"

def run_opa_eval(input_data: dict, rule: str = "allow") -> bool:
    cmd = [
        "opa", "eval",
        "-d", "policies/opa_policy.rego",
        "-I", f"data.medviet.data_access.{rule}"
    ]
    proc = subprocess.run(
        cmd,
        input=json.dumps(input_data),
        text=True,
        capture_output=True,
        check=True
    )
    res = json.loads(proc.stdout)
    if "result" in res and len(res["result"]) > 0:
        return res["result"][0]["expressions"][0]["value"]
    return False

class TestOPAPolicies:

    def test_admin_allow(self):
        # Admin is allowed to perform any action on any resource
        assert run_opa_eval({"user": {"role": "admin"}, "resource": "any", "action": "any"}) is True

    def test_ml_engineer_rules(self):
        # Allowed to read training_data and model_artifacts
        assert run_opa_eval({"user": {"role": "ml_engineer"}, "resource": "training_data", "action": "read"}) is True
        assert run_opa_eval({"user": {"role": "ml_engineer"}, "resource": "model_artifacts", "action": "write"}) is True
        # Not allowed to delete production data
        assert run_opa_eval({"user": {"role": "ml_engineer"}, "resource": "production_data", "action": "delete"}, rule="deny") is True

    def test_data_analyst_rules(self):
        # Allowed to read aggregated_metrics
        assert run_opa_eval({"user": {"role": "data_analyst"}, "resource": "aggregated_metrics", "action": "read"}) is True
        # Allowed to write reports
        assert run_opa_eval({"user": {"role": "data_analyst"}, "resource": "reports", "action": "write"}) is True
        # Denied other actions/resources
        assert run_opa_eval({"user": {"role": "data_analyst"}, "resource": "raw_patient_data", "action": "read"}) is False

    def test_intern_rules(self):
        # Allowed to access sandbox
        assert run_opa_eval({"user": {"role": "intern"}, "resource": "sandbox", "action": "any"}) is True
        # Denied other access
        assert run_opa_eval({"user": {"role": "intern"}, "resource": "production_data", "action": "read"}) is False

    def test_export_restriction(self):
        # Denied to export restricted data outside VN
        assert run_opa_eval({"data_classification": "restricted", "destination_country": "US"}, rule="deny") is True
        # Allowed to export restricted data inside VN
        assert run_opa_eval({"data_classification": "restricted", "destination_country": "VN"}, rule="deny") is False
