"""Service layer for file and workspace file operations."""

import os
from datetime import datetime
from typing import Any

from app.core.database import DatabaseManager
from app.core.exceptions import AppError
from app.core.jobs import create_embedding_job
from app.core.loader import DocumentLoader
from app.core.logger import logger
from app.core.models import FileMetadata, Workspace


class FileService:
    """
    FileService handles the lifecycle of documents in the application.

    This includes uploading, local directory processing, and deletion,
    while orchestrating background embedding jobs.
    """

    def __init__(self, db: DatabaseManager):
        """
        Initialize the file service.

        Args:
            db: Database manager instance.
        """
        self.db = db

    def upload_files(
        self,
        uploaded_files: list[Any],
        workspace: Workspace,
        embedding_settings: dict[str, Any],
    ) -> tuple[int, list[str], list[str]]:
        """
        Process uploaded files and queue them for embedding.

        Args:
            uploaded_files: List of Streamlit UploadedFile objects.
            workspace: The Target workspace.
            embedding_settings: Settings for the embedding model.

        Returns:
            Tuple[int, List[str], List[str]]: (Count of files added, success messages, error messages)
        """
        if not uploaded_files or not workspace:
            return 0, [], ["Dosya veya çalışma alanı sağlanmadı."]

        files_to_process = []
        errors = []
        successes = []

        for uploaded_file in uploaded_files:
            try:
                # 1. Validate file format and size
                is_valid, error = DocumentLoader.validate_file(uploaded_file)
                if not is_valid:
                    errors.append(f"{uploaded_file.name}: {error}")
                    continue

                # 2. Check for duplicates using content hash
                uploaded_file.seek(0)
                file_bytes = uploaded_file.read()
                file_hash = DocumentLoader.calculate_hash(file_bytes)

                existing_files = self.db.get_files(workspace.id)
                if any(f.content_hash == file_hash for f in existing_files):
                    errors.append(
                        f"{uploaded_file.name}: Bu dosya bu çalışma alanında zaten mevcut."
                    )
                    continue

                # 3. Extract text content
                uploaded_file.seek(0)
                text = DocumentLoader.load_file(uploaded_file)
                if not text or not text.strip():
                    errors.append(
                        f"{uploaded_file.name}: Metin çıkarılamadı veya dosya boş."
                    )
                    continue

                # 4. Create metadata with stable ID (scoped to workspace to allow same file in different context)
                stable_id = f"{workspace.id}_{file_hash[:20]}"
                file_meta = FileMetadata(
                    id=stable_id,
                    workspace_id=workspace.id,
                    filename=uploaded_file.name,
                    original_name=uploaded_file.name,
                    file_type=uploaded_file.name.split(".")[-1].lower(),
                    size=len(file_bytes),
                    content_hash=file_hash,
                    status="pending",
                )

                self.db.create_file(file_meta)

                files_to_process.append(
                    {
                        "id": file_meta.id,
                        "filename": uploaded_file.name,
                        "text": text,
                        "file_metadata": file_meta,
                    }
                )

            except Exception as e:
                logger.error(f"Error processing upload {uploaded_file.name}: {e}")
                errors.append(f"{uploaded_file.name} işlenirken hata oluştu.")

        if files_to_process:
            # 5. Delegate to background job worker
            create_embedding_job(
                files=files_to_process,
                workspace_id=workspace.id,
                workspace_name=workspace.name,
                db=self.db,
                embedding_settings=embedding_settings,
            )

            # 6. Update workspace metadata
            workspace.last_modified = datetime.now()
            self.db.update_workspace(workspace)
            successes.append(
                f"Başarıyla yüklendi: {len(files_to_process)} dosya! İşleme başlatıldı."
            )
            logger.info(
                f"Queued {len(files_to_process)} files for embedding in workspace {workspace.id}"
            )

        return len(files_to_process), successes, errors

    def delete_file(self, file_id: str, workspace_id: str) -> None:
        """
        Remove a file record from the database.

        Note: Vectors are preserved in Chroma for potential recovery or shared reference
        unless a hard reset is triggered.
        """
        try:
            workspace = self.db.get_workspace(workspace_id)
            if workspace:
                self.db.delete_file(file_id)
                workspace.last_modified = datetime.now()
                self.db.update_workspace(workspace)
                logger.info(f"File {file_id} deleted from workspace {workspace_id}")
        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {e}")
            raise AppError(f"Dosya silinemedi: {e}")

    def process_directory(
        self,
        directory_path: str,
        workspace: Workspace,
        embedding_settings: dict[str, Any],
    ) -> tuple[int, list[str], list[str]]:
        """
        Scan a local directory and process all supported documents.
        """
        if not directory_path or not workspace:
            return 0, [], ["Dizin yolu ve Workspace seçilmelidir."]

        errors = []
        successes = []

        try:
            loader = DocumentLoader()
            documents = loader.load_directory(directory_path)

            if not documents:
                return 0, [], ["Dizinde uygun belge bulunamadı."]

            files_to_process = []
            for doc in documents:
                try:
                    source_path = doc.metadata.get("source", "unknown")
                    original_name = os.path.basename(source_path)

                    file_meta = FileMetadata(
                        workspace_id=workspace.id,
                        filename=original_name,
                        original_name=original_name,
                        file_type=original_name.split(".")[-1].lower(),
                        size=len(doc.page_content),
                        status="pending",
                    )
                    self.db.create_file(file_meta)

                    files_to_process.append(
                        {
                            "id": file_meta.id,
                            "filename": file_meta.filename,
                            "text": doc.page_content,
                            "file_metadata": file_meta,
                        }
                    )
                except Exception as inner_e:
                    logger.warning(
                        f"Failed to process directory item {source_path}: {inner_e}"
                    )
                    errors.append(f"{original_name} işlenirken hata: {str(inner_e)}")

            if files_to_process:
                create_embedding_job(
                    files=files_to_process,
                    workspace_id=workspace.id,
                    workspace_name=workspace.name,
                    db=self.db,
                    embedding_settings=embedding_settings,
                )

                workspace.last_modified = datetime.now()
                self.db.update_workspace(workspace)
                successes.append(f"{len(files_to_process)} belge kuyruğa eklendi!")

            return len(files_to_process), successes, errors

        except Exception as e:
            logger.error(f"Directory processing failed: {e}")
            return 0, [], [f"Dizin işleme başarısız oldu: {str(e)}"]
