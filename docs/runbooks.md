# Operational Runbooks

## 🚨 HighErrorRate
**Severity**: Critical
**Threshold**: > 5% error rate for 2 minutes

**Likely Causes**:
- Unhandled exceptions in `hybrid_rank` or `tfidf_recommend`.
- Malformed inputs from frontend.
- Database query syntax errors.

**Action**:
1. Check logs: `grep "ERROR" logs/app.json | tail -n 20`
2. If `OperationalError` (DB), check database file permissions/integrity.
3. If `ValueError/KeyError` (Code), rollback to previous version via `MODEL_VERSION`.

---

## ⚠️ HighLatency
**Severity**: Warning
**Threshold**: P95 > 500ms for 5 minutes

**Likely Causes**:
- SQLite lock contention (too many concurrent writes).
- Complex TF-IDF matrix operations on CPU.
- Memory pressure causing swapping.

**Action**:
1. Check CPU/Memory usage: `top -p $(pgrep -f "uvicorn")`
2. If DB latency is high, stop background ingestion if running.
3. Consider scaling up instance or migrating to PostgreSQL.

---

## 🚨 DatabaseConnectFailure
**Severity**: Critical
**Threshold**: > 0 failures/min

**Likely Causes**:
- `movie_rec.db` deleted or permissions changed.
- Disk full.
- SQLite file corruption.

**Action**:
1. Check file existence: `ls -l movie_rec.db`
2. Check disk space: `df -h`
3. Restore DB from backup or re-run ingestion: `python data_ingestion/fetch_tmdb.py`

---

## 🚨 ModelLoadFailure
**Severity**: Critical
**Threshold**: Metric missing for 1 minute

**Likely Causes**:
- Artifacts directory missing or corrupted.
- `pickle` incompatibility (NumPy version mismatch).
- Permission denied reading artifacts.

**Action**:
1. Check startup logs for "Failed to load model".
2. Verify artifacts exist: `ls -R artifacts/tfidf/$MODEL_VERSION`
3. Re-train model: `python ml/train_tfidf.py`
