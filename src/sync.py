# src/sync.py
from pathlib import Path
import shutil
from typing import Tuple
from src.config import ONEDRIVE_STORAGE_ROOT, LOCAL_STORAGE_ROOT

def _iter_files(root: Path):
    if not root.exists():
        return
    for p in root.rglob("*"):
        if p.is_file():
            yield p

def sync_local_to_onedrive() -> Tuple[int, int]:
    if ONEDRIVE_STORAGE_ROOT is None:
        print("[sync] OneDrive not detected for user jooch  skip")
        return 0, 0

    moved, failed = 0, 0
    for src in _iter_files(LOCAL_STORAGE_ROOT):
        rel = src.relative_to(LOCAL_STORAGE_ROOT)
        dst = ONEDRIVE_STORAGE_ROOT / rel
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            # 동일 파일 있으면 덮어씀
            shutil.move(str(src), str(dst))
            moved += 1
        except Exception as e:
            print(f"[sync] failed {src} -> {dst}  {e}")
            failed += 1

    # 빈 폴더 정리
    for d in sorted(LOCAL_STORAGE_ROOT.rglob("*"), reverse=True):
        if d.is_dir():
            try:
                d.rmdir()
            except OSError:
                pass

    print(f"[sync] moved {moved}  failed {failed}")
    return moved, failed
