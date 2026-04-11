"""Background job queue and worker management."""

import queue
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any

from app.core.config import AppConfig
from app.core.config import AppConfig
from app.core.constants import ProcessingStatus
from app.core.database import DatabaseManager
from app.core.models import Job


class JobQueue:
    """Thread-safe job queue for background processing."""

    def __init__(self, max_workers: int = 2):
        self._queue: queue.Queue = queue.Queue()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._db = DatabaseManager()

    def submit_job(
        self,
        job_type: str,
        workspace_id: str,
        file_ids: list[str],
        task_func: Callable,
        task_args: tuple = (),
        task_kwargs: dict | None = None,
    ) -> Job:
        """Submit a new job to the queue."""
        if task_kwargs is None:
            task_kwargs = {}

        # Create job object
        job = Job(
            job_type=job_type,
            workspace_id=workspace_id,
            file_ids=file_ids,
            status=ProcessingStatus.PENDING,
            total=len(file_ids) if file_ids else 1,
            current=0,
            progress=0.0,
        )

        # Save to database
        self._db.jobs.create(job)

        # Store in memory
        with self._lock:
            self._jobs[job.id] = job

        # Create future
        self._executor.submit(
            self._run_job, job, task_func, task_args, task_kwargs
        )

        return job

    def _run_job(
        self, job: Job, task_func: Callable, task_args: tuple, task_kwargs: dict
    ):
        """Run a job in the background."""
        job.status = ProcessingStatus.RUNNING
        job.started_at = datetime.now()
        self._db.jobs.update(job)

        try:
            # Update progress callback
            def update_progress(current: int, total: int, message: str = ""):
                job.current = current
                job.total = total
                job.progress = (current / total) * 100 if total > 0 else 0
                if message:
                    job.error_message = message
                self._db.jobs.update(job)

            # Run the task
            result = task_func(
                *task_args, progress_callback=update_progress, **task_kwargs
            )

            # Mark as completed
            job.status = ProcessingStatus.COMPLETED
            job.progress = 100.0
            job.current = job.total
            job.completed_at = datetime.now()
            self._db.jobs.update(job)

            return result

        except Exception as e:
            job.status = ProcessingStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
            self._db.jobs.update(job)
            raise

    def get_job(self, job_id: str) -> Job | None:
        """Get a job by ID."""
        with self._lock:
            return self._jobs.get(job_id)

    def get_active_jobs(self, workspace_id: str | None = None) -> list[Job]:
        """Get all active (pending/running) jobs."""
        with self._lock:
            jobs = list(self._jobs.values())

        if workspace_id:
            jobs = [j for j in jobs if j.workspace_id == workspace_id]

        return [j for j in jobs if j.status in ("pending", "running")]

    def get_job_status(self, job_id: str) -> Job | None:
        """Get job status from database."""
        job = self._db.jobs.get_by_id(job_id)
        if job:
            with self._lock:
                self._jobs[job.id] = job
            return job
        return None

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job (can't cancel running jobs)."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job and job.status == ProcessingStatus.PENDING:
                job.status = ProcessingStatus.CANCELLED
                job.completed_at = datetime.now()
                self._db.jobs.update(job)
                return True
        return False

    def shutdown(self):
        """Shutdown the executor."""
        self._executor.shutdown(wait=True)


# Global job queue instance
_job_queue: JobQueue | None = None


def get_job_queue() -> JobQueue:
    """Get or create the global job queue."""
    global _job_queue
    if _job_queue is None:
        _job_queue = JobQueue(max_workers=2)
    return _job_queue


class EmbeddingWorker:
    """Worker for processing document embeddings."""

    def __init__(self, embedding_manager, chunk_manager, chroma_manager):
        self.embedding_manager = embedding_manager
        self.chunk_manager = chunk_manager
        self.chroma_manager = chroma_manager

    def process_files(
        self,
        files: list[Any],
        workspace_id: str,
        workspace_name: str,
        db: DatabaseManager,
        embedding_settings: dict[str, Any] | None = None,
        progress_callback: Callable | None = None,
    ) -> dict[str, Any]:
        """Process files: chunk, embed, and upsert to Chroma."""

        results = {"success": [], "failed": []}

        total_files = len(files)

        for idx, file_data in enumerate(files):
            try:
                # Update progress
                if progress_callback:
                    progress_callback(
                        idx,
                        total_files,
                        f"İşleniyor: {file_data.get('filename', 'Dosya')}",
                    )

                # Get file metadata from DB
                file_meta = file_data.get("file_metadata")
                if not file_meta:
                    continue

                # Update file status
                file_meta.status = ProcessingStatus.PROCESSING
                db.files.update(file_meta)

                # Check if Chroma already has chunks for this stable ID
                existing_chunks = None
                collection = self.chroma_manager.get_collection(
                    workspace_id, workspace_name
                )
                if collection:
                    try:
                        # Get a sample to see if it exists
                        existing = collection.get(
                            where={"file_id": file_meta.id}, limit=1
                        )
                        if existing and existing.get("ids"):
                            # It exists! We can skip embedding if we find all chunks?
                            # For simplicity, if at least one chunk exists, we check the count
                            all_existing = collection.get(
                                where={"file_id": file_meta.id}
                            )
                            existing_chunks = all_existing.get("ids")
                    except Exception:
                        pass

                if existing_chunks:
                    # Skip embedding, just update metadata
                    chunks_count = len(existing_chunks)
                    if progress_callback:
                        progress_callback(
                            idx,
                            total_files,
                            f"Mevcut vektörler kullanılıyor: {file_data.get('filename')}",
                        )
                else:
                    # Chunk the text
                    chunks = self.chunk_manager.chunk_text(file_data.get("text", ""))
                    chunks_count = len(chunks)

                    # Get embeddings
                    if chunks:
                        embeddings = self.embedding_manager.get_embeddings(chunks)

                        # Upsert to Chroma
                        self.chroma_manager.add_chunks(
                            workspace_id=workspace_id,
                            workspace_name=workspace_name,
                            file_id=file_meta.id,
                            chunks=chunks,
                            embeddings=embeddings,
                            source=file_meta.original_name,
                        )

                # Update file status
                file_meta.status = ProcessingStatus.PROCESSED
                file_meta.chunk_count = chunks_count
                file_meta.processed_at = datetime.now()
                db.files.update(file_meta)

                results["success"].append(file_meta.id)

            except Exception as e:
                # Mark file as failed
                if file_meta:
                    file_meta.status = ProcessingStatus.ERROR
                    file_meta.error_message = str(e)
                    db.files.update(file_meta)

                results["failed"].append(
                    {"file_id": file_data.get("id"), "error": str(e)}
                )

        # Final progress update
        if progress_callback:
            progress_callback(total_files, total_files, "Tamamlandı")

        return results


def create_embedding_job(
    files: list[Any],
    workspace_id: str,
    workspace_name: str,
    db: DatabaseManager,
    embedding_settings: dict[str, Any] | None = None,
) -> Job:
    """Create a background job for embedding processing."""
    from app.core.chroma import ChromaManager, ChunkManager, EmbeddingManager

    # Initialize managers with settings if provided
    if embedding_settings:
        embedding_manager = EmbeddingManager(
            use_huggingface=embedding_settings.get("use_huggingface", False),
            ollama_model=embedding_settings.get("model_name", "nomic-embed-text"),
            ollama_url=embedding_settings.get("ollama_url", "http://localhost:11434"),
            hf_model=embedding_settings.get(
                "model_name", "sentence-transformers/all-MiniLM-L6-v2"
            ),
        )
    else:
        embedding_manager = EmbeddingManager()

    # Dynamic chunking strategy (Default to config or provided settings)
    ui_chunk_size = embedding_settings.get("chunk_size") if embedding_settings else None
    ui_chunk_overlap = (
        embedding_settings.get("chunk_overlap") if embedding_settings else None
    )

    config = AppConfig()

    chunk_size = ui_chunk_size or config.CHUNK_SIZE
    chunk_overlap = ui_chunk_overlap or config.CHUNK_OVERLAP

    if (
        embedding_settings
        and embedding_settings.get("use_huggingface")
        and not ui_chunk_size
    ):
        # Fallback for HF if no custom size provided
        chunk_size = 500
        chunk_overlap = 50

    chunk_manager = ChunkManager(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    chroma_path = (
        embedding_settings.get("chroma_path", config.CHROMA_PERSIST_DIR)
        if embedding_settings
        else config.CHROMA_PERSIST_DIR
    )
    chroma_manager = ChromaManager(persist_directory=chroma_path)

    worker = EmbeddingWorker(embedding_manager, chunk_manager, chroma_manager)
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
            "db": db,
            "embedding_settings": embedding_settings,
        },
    )
