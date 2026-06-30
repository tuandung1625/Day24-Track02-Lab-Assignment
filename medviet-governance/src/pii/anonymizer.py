import random
import hashlib
import pandas as pd
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from faker import Faker
from .detector import build_vietnamese_analyzer, detect_pii

fake = Faker("vi_VN")

class MedVietAnonymizer:

    def __init__(self):
        self.analyzer = build_vietnamese_analyzer()
        self.anonymizer = AnonymizerEngine()

    def anonymize_text(self, text: str, strategy: str = "replace") -> str:
        """
        TODO: Anonymize text với strategy được chọn.

        Strategies:
        - "mask"    : Nguyen Van A → N****** V** A
        - "replace" : thay bằng fake data (dùng Faker)
        - "hash"    : SHA-256 one-way hash
        - "generalize": chỉ dùng cho tuổi/năm sinh
        """
        results = detect_pii(text, self.analyzer)
        if not results:
            return text

        # TODO: implement operators dict dựa trên strategy
        operators = {}

        if strategy == "replace":
            operators = {
                "PERSON": OperatorConfig("custom", {"lambda": lambda x: fake.name()}),
                "EMAIL_ADDRESS": OperatorConfig("custom", {"lambda": lambda x: fake.email()}),
                "VN_CCCD": OperatorConfig("custom", {"lambda": lambda x: fake.numerify("############")}),
                "VN_PHONE": OperatorConfig("custom", {"lambda": lambda x: f"0{random.choice([3,5,7,8,9])}" + fake.numerify("########")}),
            }
        elif strategy == "mask":
            def mask_person(name):
                return " ".join([w[0] + "*" * (len(w) - 1) if len(w) > 1 else w for w in name.split()])

            def mask_email(email):
                if "@" in email:
                    local, domain = email.split("@", 1)
                    if len(local) > 1:
                        return local[0] + "*" * (len(local) - 1) + "@" + domain
                    return email
                return email

            operators = {
                "PERSON": OperatorConfig("custom", {"lambda": mask_person}),
                "EMAIL_ADDRESS": OperatorConfig("custom", {"lambda": mask_email}),
                "VN_CCCD": OperatorConfig("custom", {"lambda": lambda x: "*" * (len(x) - 3) + x[-3:]}),
                "VN_PHONE": OperatorConfig("custom", {"lambda": lambda x: x[:3] + "*" * (len(x) - 6) + x[-3:]}),
            }
        elif strategy == "hash":
            operators = {
                "PERSON": OperatorConfig("custom", {"lambda": lambda x: hashlib.sha256(x.encode()).hexdigest()}),
                "EMAIL_ADDRESS": OperatorConfig("custom", {"lambda": lambda x: hashlib.sha256(x.encode()).hexdigest()}),
                "VN_CCCD": OperatorConfig("custom", {"lambda": lambda x: hashlib.sha256(x.encode()).hexdigest()}),
                "VN_PHONE": OperatorConfig("custom", {"lambda": lambda x: hashlib.sha256(x.encode()).hexdigest()}),
            }

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators
        )
        return anonymized.text

    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        TODO: Anonymize toàn bộ DataFrame.
        - Cột text (ho_ten, dia_chi, email): dùng anonymize_text()
        - Cột cccd, so_dien_thoai: replace trực tiếp bằng fake data
        - Cột benh, ket_qua_xet_nghiem: GIỮ NGUYÊN (cần cho model training)
        - Cột patient_id: GIỮ NGUYÊN (pseudonym đã đủ an toàn)
        """
        df_anon = df.copy()

        # TODO: Xử lý từng cột PII
        # Gợi ý: dùng df.apply() hoặc list comprehension
        if "ho_ten" in df_anon.columns:
            df_anon["ho_ten"] = df_anon["ho_ten"].astype(str).apply(lambda x: self.anonymize_text(x, strategy="replace"))
        if "dia_chi" in df_anon.columns:
            df_anon["dia_chi"] = df_anon["dia_chi"].astype(str).apply(lambda x: self.anonymize_text(x, strategy="replace"))
        if "email" in df_anon.columns:
            df_anon["email"] = df_anon["email"].astype(str).apply(lambda x: self.anonymize_text(x, strategy="replace"))
        if "bac_si_phu_trach" in df_anon.columns:
            df_anon["bac_si_phu_trach"] = df_anon["bac_si_phu_trach"].astype(str).apply(lambda x: self.anonymize_text(x, strategy="replace"))

        if "cccd" in df_anon.columns:
            df_anon["cccd"] = df_anon["cccd"].apply(lambda x: fake.numerify("############"))
        if "so_dien_thoai" in df_anon.columns:
            df_anon["so_dien_thoai"] = df_anon["so_dien_thoai"].apply(
                lambda x: f"0{random.choice([3,5,7,8,9])}" + fake.numerify("########")
            )

        return df_anon

    def calculate_detection_rate(self, 
                                  original_df: pd.DataFrame,
                                  pii_columns: list) -> float:
        """
        TODO: Tính % PII được detect thành công.
        Mục tiêu: > 95%

        Logic: với mỗi ô trong pii_columns,
               kiểm tra xem detect_pii() có tìm thấy ít nhất 1 entity không.
        """
        total = 0
        detected = 0

        for col in pii_columns:
            for value in original_df[col].astype(str):
                val = value.split('.')[0]
                if col == "cccd":
                    val = val.zfill(12)
                elif col == "so_dien_thoai":
                    val = val.zfill(10)
                else:
                    val = value

                total += 1
                results = detect_pii(val, self.analyzer)
                if len(results) > 0:
                    detected += 1

        return detected / total if total > 0 else 0.0