# src/config.py
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 환경변수 또는 .env의 사용자 지정 경로를 최우선으로 허용
def load_env_override() -> Path | None:
    val = os.environ.get("FINANCEPROJ_STORAGE")
    if not val:
        env_path = PROJECT_ROOT / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() == "FINANCEPROJ_STORAGE":
                    val = v.strip().strip('"').strip("'")
                    break
    if val and Path(val).exists():
        return Path(val)
    return None

def detect_onedrive_root() -> Path | None:
    od_env = os.environ.get("OneDrive") or os.environ.get("OneDriveCommercial")
    if od_env:
        od_path = Path(od_env)
        # 1) 사용자 폴더명 검사
        if "jooch" in str(od_path):
            # 2) 프로젝트 폴더로 경로 확장
            proj_path = od_path / "coding_Projects" / "financeProj" / "finance_dashboard_data"
            proj_path.mkdir(parents=True, exist_ok=True)
            return proj_path
    return None

# 공개 경로들
ENV_STORAGE_ROOT = load_env_override()
ONEDRIVE_STORAGE_ROOT = detect_onedrive_root()
LOCAL_STORAGE_ROOT = PROJECT_ROOT / "local_storage"

# 실행 시 사용할 현재 저장 루트
if ENV_STORAGE_ROOT is not None:
    STORAGE_ROOT = ENV_STORAGE_ROOT
elif ONEDRIVE_STORAGE_ROOT is not None:
    STORAGE_ROOT = ONEDRIVE_STORAGE_ROOT
else:
    STORAGE_ROOT = LOCAL_STORAGE_ROOT

DATA_RAW = STORAGE_ROOT / "data" / "raw"
DATA_PROCESSED = STORAGE_ROOT / "data" / "processed"
CHARTS = STORAGE_ROOT / "charts"

def ensure_dirs() -> None:
    for p in [DATA_RAW, DATA_PROCESSED, CHARTS]:
        p.mkdir(parents=True, exist_ok=True)

print(f"[config] STORAGE_ROOT = {STORAGE_ROOT}")
print(f"[config] ONEDRIVE_STORAGE_ROOT = {ONEDRIVE_STORAGE_ROOT}")
print(f"[config] LOCAL_STORAGE_ROOT = {LOCAL_STORAGE_ROOT}")
