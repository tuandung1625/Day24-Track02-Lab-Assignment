import pytest
import os
import pandas as pd
from src.quality.validation import build_patient_expectation_suite, validate_anonymized_data
from src.pii.anonymizer import MedVietAnonymizer

class TestDataValidation:

    def test_build_expectation_suite(self):
        # Verify that we can build the expectation suite without errors
        suite = build_patient_expectation_suite()
        assert suite is not None
        assert suite.name == "patient_data_suite"
        assert len(suite.expectations) >= 6

    def test_validate_anonymized_data_success(self, tmp_path):
        # 1. Load original data and anonymize
        raw_df = pd.read_csv("data/raw/patients_raw.csv")
        anonymizer = MedVietAnonymizer()
        df_anon = anonymizer.anonymize_dataframe(raw_df)

        # Save to temp file
        temp_csv = tmp_path / "patients_anonymized.csv"
        df_anon.to_csv(temp_csv, index=False)

        # 2. Run validation
        results = validate_anonymized_data(str(temp_csv))
        
        # 3. Assertions
        assert results["success"] is True
        assert len(results["failed_checks"]) == 0
        assert results["stats"]["total_rows"] == len(raw_df)

    def test_validate_anonymized_data_cccd_leakage(self, tmp_path):
        raw_df = pd.read_csv("data/raw/patients_raw.csv")
        anonymizer = MedVietAnonymizer()
        df_anon = anonymizer.anonymize_dataframe(raw_df)

        # Intentionally leak a raw CCCD value into the anonymized data
        raw_cccd = raw_df.loc[0, "cccd"]
        df_anon.loc[0, "cccd"] = raw_cccd

        # Save to temp file
        temp_csv = tmp_path / "patients_leaked.csv"
        df_anon.to_csv(temp_csv, index=False)

        results = validate_anonymized_data(str(temp_csv))
        assert results["success"] is False
        assert any("contains" in check and "original CCCD" in check for check in results["failed_checks"])

    def test_validate_anonymized_data_nulls_and_rows(self, tmp_path):
        raw_df = pd.read_csv("data/raw/patients_raw.csv")
        anonymizer = MedVietAnonymizer()
        df_anon = anonymizer.anonymize_dataframe(raw_df)

        # Intentionally inject null values and remove a row
        df_anon.loc[df_anon.index[1], "ho_ten"] = None
        df_anon = df_anon.iloc[1:] # Drop first row to cause row count mismatch

        # Save to temp file
        temp_csv = tmp_path / "patients_invalid.csv"
        df_anon.to_csv(temp_csv, index=False)

        results = validate_anonymized_data(str(temp_csv))
        assert results["success"] is False
        assert any("has 1 null values" in check for check in results["failed_checks"])
        assert any("Row count mismatch" in check for check in results["failed_checks"])
