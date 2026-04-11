import sys

sys.path.insert(0, ".")

# Test embedding directly

from app.core.database import DatabaseManager
from app.core.jobs import create_embedding_job
from app.core.models import FileMetadata, Workspace

# Create a test workspace
db = DatabaseManager()
workspace = Workspace(name="test_embed")
db.create_workspace(workspace)

# Create a test file
file_meta = FileMetadata(
    workspace_id=workspace.id,
    filename="test.txt",
    original_name="test.txt",
    file_type="txt",
    content_hash="test123",
    status="pending",
)
db.create_file(file_meta)

print(f"Created workspace: {workspace.id}")
print(f"Created file: {file_meta.id}")

# Try to create an embedding job
files_to_process = [
    {
        "id": file_meta.id,
        "filename": "test.txt",
        "text": "This is a test document for embedding.",
        "file_metadata": file_meta,
    }
]

# Try to run embedding job
embedding_settings = {
    "use_huggingface": False,
    "model_name": "nomic-embed-text",
    "ollama_url": "http://localhost:11434",
    "chunk_size": 1000,
    "chunk_overlap": 200,
}

try:
    job = create_embedding_job(
        files=files_to_process,
        workspace_id=workspace.id,
        workspace_name=workspace.name,
        db=db,
        embedding_settings=embedding_settings,
    )
    print(f"Job created: {job.id}")
    print(f"Job status: {job.status}")

    # Wait and check multiple times
    import time

    for i in range(10):
        time.sleep(2)

        # Get all jobs and find ours
        jobs = db.get_jobs()
        our_job = next((j for j in jobs if j.id == job.id), None)

        if our_job:
            print(
                f"Check {i + 1}: Status={our_job.status}, Progress={our_job.progress}%"
            )
            if our_job.error_message:
                print(f"  Error: {our_job.error_message[:200]}")
            if our_job.status in ["completed", "failed"]:
                break

    # Final status
    jobs = db.get_jobs()
    our_job = next((j for j in jobs if j.id == job.id), None)
    if our_job:
        print(f"\nFinal status: {our_job.status}")
        print(f"Final progress: {our_job.progress}%")
        if our_job.error_message:
            print(f"Error: {our_job.error_message}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback

    traceback.print_exc()
