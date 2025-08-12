from pathlib import Path

# OneDrive 기본 경로 (Windows, 주찬님 계정 적용)
ONEDRIVE_PATH = Path(r"C:\Users\jooch\OneDrive\coding_Projects\financeProj\finance_dashboard_data")

# 데이터 저장 경로
DATA_RAW = ONEDRIVE_PATH / "data" / "raw"
DATA_PROCESSED = ONEDRIVE_PATH / "data" / "processed"
CHARTS = ONEDRIVE_PATH / "charts"

# 폴더 없으면 생성
for folder in [DATA_RAW, DATA_PROCESSED, CHARTS]:
    folder.mkdir(parents=True, exist_ok=True)