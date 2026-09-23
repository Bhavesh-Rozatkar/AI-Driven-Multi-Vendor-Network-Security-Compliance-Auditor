import os
from pathlib import Path
BASE_DIR=Path(__file__).resolve().parents[2];DATA_DIR=BASE_DIR/'data';BENCHMARK_DIR=DATA_DIR/'benchmarks';UPLOAD_DIR=DATA_DIR/'benchmark_uploads';AUDIT_DIR=DATA_DIR/'audit';SNAPSHOT_DIR=DATA_DIR/'snapshots'
for p in (BENCHMARK_DIR,UPLOAD_DIR,AUDIT_DIR,SNAPSHOT_DIR):p.mkdir(parents=True,exist_ok=True)
MAX_UPLOAD_MB=int(os.getenv('MAX_BENCHMARK_UPLOAD_MB','15'))
