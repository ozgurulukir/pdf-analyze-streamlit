import sys

sys.path.insert(0, ".")

from app.core.database import DatabaseManager

db = DatabaseManager()
jobs = db.get_jobs()
print(f"Total jobs: {len(jobs)}")
for job in jobs[-5:]:
    print(
        f"  - {job.id[:20]}...: {job.job_type} - {job.status} - Progress: {job.progress}%"
    )
    if job.error_message:
        print(f"    Error: {job.error_message[:100]}")
