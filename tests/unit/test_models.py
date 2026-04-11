"""Unit tests for core models."""

import pytest

from app.core.models import (
    FileMetadataModel,
    JobModel,
    MessageModel,
    UserPreferencesModel,
    WorkspaceModel,
)


class TestWorkspaceModel:
    """Tests for WorkspaceModel."""

    def test_create_workspace(self):
        """Test creating a workspace."""
        ws = WorkspaceModel(name="Test Workspace")
        assert ws.name == "Test Workspace"
        assert ws.id is not None
        assert ws.file_count == 0
        assert ws.is_active is False

    def test_workspace_validation_name_required(self):
        """Test workspace name validation."""
        with pytest.raises(ValueError):
            WorkspaceModel(name="")

    def test_workspace_name_strip(self):
        """Test workspace name whitespace stripping."""
        ws = WorkspaceModel(name="  Test  ")
        assert ws.name == "Test"

    def test_workspace_to_dict(self):
        """Test workspace serialization."""
        ws = WorkspaceModel(name="Test", description="A test workspace")
        data = ws.to_dict()
        assert data["name"] == "Test"
        assert data["description"] == "A test workspace"

    def test_workspace_from_dict(self):
        """Test workspace deserialization."""
        data = {
            "id": "test-id",
            "name": "Test",
            "description": "Test desc",
            "file_count": 5,
        }
        ws = WorkspaceModel.from_dict(data)
        assert ws.id == "test-id"
        assert ws.name == "Test"
        assert ws.file_count == 5


class TestFileMetadataModel:
    """Tests for FileMetadataModel."""

    def test_create_file(self):
        """Test creating a file record."""
        file = FileMetadataModel(
            workspace_id="ws-1",
            filename="test.pdf",
            original_name="test.pdf",
            file_type="pdf",
            size=1024,
        )
        assert file.filename == "test.pdf"
        assert file.status == "pending"
        assert file.workspace_id == "ws-1"

    def test_file_type_validation(self):
        """Test file type validation."""
        with pytest.raises(ValueError):
            FileMetadataModel(
                workspace_id="ws-1",
                filename="test.exe",
                original_name="test.exe",
                file_type="exe",
                size=1024,
            )

    def test_file_size_validation(self):
        """Test file size validation."""
        with pytest.raises(ValueError):
            FileMetadataModel(
                workspace_id="ws-1",
                filename="test.pdf",
                original_name="test.pdf",
                file_type="pdf",
                size=999999999999999,  # Exceeds max
            )

    def test_status_validation(self):
        """Test status validation."""
        with pytest.raises(ValueError):
            FileMetadataModel(
                workspace_id="ws-1",
                filename="test.pdf",
                file_type="pdf",
                status="invalid_status",
            )


class TestMessageModel:
    """Tests for MessageModel."""

    def test_create_message(self):
        """Test creating a message."""
        msg = MessageModel(role="user", content="Hello, world!")
        assert msg.role == "user"
        assert msg.content == "Hello, world!"

    def test_role_validation(self):
        """Test role validation."""
        with pytest.raises(ValueError):
            MessageModel(role="invalid", content="test")

    def test_content_max_length(self):
        """Test content length validation."""
        with pytest.raises(ValueError):
            MessageModel(
                role="user",
                content="x" * 50001,  # Exceeds max
            )


class TestUserPreferencesModel:
    """Tests for UserPreferencesModel."""

    def test_create_preferences(self):
        """Test creating preferences."""
        prefs = UserPreferencesModel()
        assert "concise" in prefs.weights
        assert prefs.weights["concise"] == 0.5

    def test_weight_validation(self):
        """Test weight range validation."""
        with pytest.raises(ValueError):
            UserPreferencesModel(weights={"test": 2.0})  # Exceeds 1.0

    def test_weight_clamp(self):
        """Test weight clamping in valid range."""
        prefs = UserPreferencesModel(weights={"test": 0.5})
        assert prefs.weights["test"] == 0.5


class TestJobModel:
    """Tests for JobModel."""

    def test_create_job(self):
        """Test creating a job."""
        job = JobModel(job_type="embedding", workspace_id="ws-1", file_ids=["file-1"])
        assert job.job_type == "embedding"
        assert job.status == "pending"
        assert job.progress == 0.0

    def test_job_progress_validation(self):
        """Test progress validation."""
        # Test clamping during instantiation
        job1 = JobModel(job_type="test", progress=1.5)
        assert job1.progress == 1.0

        job2 = JobModel(job_type="test", progress=-0.5)
        assert job2.progress == 0.0

    def test_job_is_complete(self):
        """Test job completion check."""
        job_pending = JobModel(job_type="test", status="pending")
        assert job_pending.is_complete() is False

        job_completed = JobModel(job_type="test", status="completed")
        assert job_completed.is_complete() is True

        job_failed = JobModel(job_type="test", status="failed")
        assert job_failed.is_complete() is True
