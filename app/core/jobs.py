"""Background job queue and worker management."""
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor, Future
from typing import List, Optional, Callable, Dict, Any
import streamlit as st

from app.core.models import Job
from app.core.database import DatabaseManager
from datetime import datetime


class JobQueue:
    """Thread-safe job queue for background processing."""

    def __init__(self, max_workers: int = 2):
        self._queue: queue.Queue = queue.Queue()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()
        self._db = DatabaseManager()

    def submit_job(
        self,
        job_type: str,
        workspace_id: str,
        file_ids: List[str],
        task_func: Callable,
        task_args: tuple = (),
        task_kwargs: dict = None
    ) -> Job:
        """Submit a new job to the queue."""
        if task_kwargs is None:
            task_kwargs = {}

        # Create job object
        job = Job(
            job_type=job_type,
            workspace_id=workspace_id,
            file_ids=file_ids,
            status="pending",
            total=len(file_ids) if file_ids else 1,
            current=0,
            progress=0.0
        )

        # Save to database
        self._db.create_job(job)

        # Store in memory
        with self._lock:
            self._jobs[job.id] = job

        # Create future
        future = self._executor.submit(
            self._run_job,
            job,
            task_func,
            task_args,
            task_kwargs
        )

        return job

    def _run_job(
        self,
        job: Job,
        task_func: Callable,
        task_args: tuple,
        task_kwargs: dict
    ):
        """Run a job in the background."""
        job.status = "running"
        job.started_at = datetime.now()
        self._db.update_job(job)

        try:
            # Update progress callback
            def update_progress(current: int, total: int, message: str = ""):
                job.current = current
                job.total = total
                job.progress = (current / total) * 100 if total > 0 else 0
                if message:
                    job.error_message = message
                self._db.update_job(job)

            # Run the task
            result = task_func(
                *task_args,
                progress_callback=update_progress,
                **task_kwargs
            )

            # Mark as completed
            job.status = "completed"
            job.progress = 100.0
            job.current = job.total
            job.completed_at = datetime.now()
            self._db.update_job(job)

            return result

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now()
            self._db.update_job(job)
            raise

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        with self._lock:
            return self._jobs.get(job_id)

    def get_active_jobs(self, workspace_id: Optional[str] = None) -> List[Job]:
        """Get all active (pending/running) jobs."""
        with self._lock:
            jobs = list(self._jobs.values())
        
        if workspace_id:
            jobs = [j for j in jobs if j.workspace_id == workspace_id]
        
        return [j for j in jobs if j.status in ("pending", "running")]

    def get_job_status(self, job_id: str) -> Optional[Job]:
        """Get job status from database."""
        jobs = self._db.get_jobs()
        for job in jobs:
            if job.id == job_id:
                with self._lock:
                    self._jobs[job.id] = job
                return job
        return None

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job (can't cancel running jobs)."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job and job.status == "pending":
                job.status = "cancelled"
                job.completed_at = datetime.now()
                self._db.update_job(job)
                return True
        return False

    def shutdown(self):
        """Shutdown the executor."""
        self._executor.shutdown(wait=True)


# Global job queue instance
_job_queue: Optional[JobQueue] = None


def get_job_queue() -> JobQueue:
    """Get or create the global job queue."""
    global _job_queue
    if _job_queue is None:
        _job_queue = JobQueue(max_workers=2)
    return _job_queue


class EmbeddingWorker:
    """Worker for processing document embeddings."""

    def __init__(self):
        self.chroma_manager = None
        self.embedding_manager = None
        self.chunk_manager = None

    def process_files(
        self,
        files: List[Any],
        workspace_id: str,
        workspace_name: str,
        db: DatabaseManager,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Process files: chunk, embed, and upsert to Chroma."""
        from app.core.chroma import EmbeddingManager, ChunkManager, ChromaManager
        from app.core.models import FileMetadata

        results = {
            "success": [],
            "failed": []
        }

        # Initialize managers
        self.embedding_manager = EmbeddingManager()
        self.chunk_manager = ChunkManager()
        self.chroma_manager = ChromaManager()

        total_files = len(files)
        
        for idx, file_data in enumerate(files):
            try:
                # Update progress
                if progress_callback:
                    progress_callback(idx, total_files, f"İşleniyor: {file_data.get('filename', 'Dosya')}")

                # Get file metadata from DB
                file_meta = file_data.get("file_metadata")
                if not file_meta:
                    continue

                # Update file status
                file_meta.status = "processing"
                db.update_file(file_meta)

                # Chunk the text
                chunks = self.chunk_manager.chunk_text(file_data.get("text", ""))
                
                # Get embeddings
                if chunks:
                    embeddings = self.embedding_manager.get_embeddings(chunks)
                    
                    # Upsert to Chroma
                    chroma_ids = self.chroma_manager.add_chunks(
                        workspace_id=workspace_id,
                        workspace_name=workspace_name,
                        file_id=file_meta.id,
                        chunks=chunks,
                        embeddings=embeddings
                    )

                # Update file status
                file_meta.status = "processed"
                file_meta.chunk_count = len(chunks)
                file_meta.processed_at = datetime.now()
                db.update_file(file_meta)

                results["success"].append(file_meta.id)

            except Exception as e:
                # Mark file as failed
                if file_meta:
                    file_meta.status = "error"
                    file_meta.error_message = str(e)
                    db.update_file(file_meta)
                
                results["failed"].append({
                    "file_id": file_data.get("id"),
                    "error": str(e)
                })

        # Final progress update
        if progress_callback:
            progress_callback(total_files, total_files, "Tamamlandı")

        return results


def create_embedding_job(
    files: List[Any],
    workspace_id: str,
    workspace_name: str,
    db: DatabaseManager
) -> Job:
    """Create a background job for embedding processing."""
    worker = EmbeddingWorker()
    job_queue = get_job_queue()

    return job_queue.submit_job(
        job_type="embed",
        workspace_id=workspace_id,
        file_ids=[f.get("id") for f in files],
        task_func=worker.process_files,
        task_kwargs={
            "files": files,
            "workspace_id": workspace_id,
            "workspace_name": workspace_name,
            "db": db
        }
    )
