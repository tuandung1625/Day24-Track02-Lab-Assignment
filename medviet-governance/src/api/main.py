# src/api/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
from src.access.rbac import get_current_user, require_permission
from src.pii.anonymizer import MedVietAnonymizer

app = FastAPI(title="MedViet Data API", version="1.0.0")
anonymizer = MedVietAnonymizer()

# --- ENDPOINT 1 ---
@app.get("/api/patients/raw")
@require_permission(resource="patient_data", action="read")
async def get_raw_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    TODO: Trả về raw patient data (chỉ admin được phép).
    Load từ data/raw/patients_raw.csv
    Trả về 10 records đầu tiên dưới dạng JSON.
    """
    try:
        df = pd.read_csv("data/raw/patients_raw.csv")
        # Format columns for consistent display (e.g. zfill)
        if "cccd" in df.columns:
            df["cccd"] = df["cccd"].astype(str).str.split('.').str[0].str.zfill(12)
        if "so_dien_thoai" in df.columns:
            df["so_dien_thoai"] = df["so_dien_thoai"].astype(str).str.split('.').str[0].str.zfill(10)
        
        data = df.head(10).to_dict(orient="records")
        return JSONResponse(content={"data": data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ENDPOINT 2 ---
@app.get("/api/patients/anonymized")
@require_permission(resource="training_data", action="read")
async def get_anonymized_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    TODO: Trả về anonymized data (ml_engineer và admin được phép).
    Load raw data → anonymize → trả về JSON.
    """
    try:
        df = pd.read_csv("data/raw/patients_raw.csv")
        df_anon = anonymizer.anonymize_dataframe(df)
        data = df_anon.to_dict(orient="records")
        return JSONResponse(content={"data": data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ENDPOINT 3 ---
@app.get("/api/metrics/aggregated")
@require_permission(resource="aggregated_metrics", action="read")
async def get_aggregated_metrics(
    current_user: dict = Depends(get_current_user)
):
    """
    TODO: Trả về aggregated metrics (data_analyst, ml_engineer, admin).
    Ví dụ: số bệnh nhân theo từng loại bệnh (không có PII).
    """
    try:
        df = pd.read_csv("data/raw/patients_raw.csv")
        metrics = df.groupby("benh").size().to_dict()
        return JSONResponse(content={"metrics": metrics})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ENDPOINT 4 ---
@app.delete("/api/patients/{patient_id}")
@require_permission(resource="patient_data", action="delete")
async def delete_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    TODO: Chỉ admin được xóa. Các role khác nhận 403.
    """
    return {"message": f"Patient '{patient_id}' deleted successfully"}

@app.get("/health")
async def health():
    return {"status": "ok", "service": "MedViet Data API"}