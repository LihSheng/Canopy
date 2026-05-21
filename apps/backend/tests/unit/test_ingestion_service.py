from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from common.errors import ValidationError
from ingestion.domain import UploadRecord, UploadStatus
from ingestion.service import process_upload


class TestProcessUpload:
    def test_rejects_unsupported_extension(self):
        mock_repo = MagicMock()
        with pytest.raises(ValidationError, match="Unsupported file type"):
            process_upload(
                repo=mock_repo,
                file_bytes=b"dummy",
                file_name="data.pdf",
                source_profile="herdhr",
                dataset_type="payroll",
            )
        mock_repo.save_upload.assert_not_called()

    def test_rejects_oversized_file(self):
        mock_repo = MagicMock()
        large = b"x" * (51 * 1024 * 1024)
        with pytest.raises(ValidationError, match="exceeds maximum size"):
            process_upload(
                repo=mock_repo,
                file_bytes=large,
                file_name="data.xlsx",
                source_profile="herdhr",
                dataset_type="payroll",
            )
        mock_repo.save_upload.assert_not_called()

    @patch("ingestion.service._get_upload_dir")
    @patch("ingestion.service._compute_checksum")
    def test_stores_file_and_returns_record(self, mock_checksum, mock_get_dir, tmp_path):
        mock_get_dir.return_value = tmp_path
        mock_checksum.return_value = "abc123"

        mock_repo = MagicMock()
        mock_repo.save_upload.side_effect = lambda r: r

        result = process_upload(
            repo=mock_repo,
            file_bytes=b"hello,world",
            file_name="data.csv",
            source_profile="herdhr",
            dataset_type="payroll",
        )

        assert result.file_name == "data.csv"
        assert result.status == UploadStatus.uploaded
        assert result.checksum == "abc123"

        saved_path = tmp_path / f"{result.id}.csv"
        assert saved_path.exists()
        assert saved_path.read_bytes() == b"hello,world"

        mock_repo.save_upload.assert_called_once()

    def test_accepts_supported_extensions(self):
        mock_repo = MagicMock()

        def fake_save(record: UploadRecord) -> UploadRecord:
            record.id = "test-uuid"
            return record

        mock_repo.save_upload.side_effect = fake_save

        for ext in [".xlsx", ".xls", ".xlsm", ".csv"]:
            with patch("ingestion.service._get_upload_dir", return_value=Path(__file__).parent):
                with patch("ingestion.service._compute_checksum", return_value="x"):
                    result = process_upload(
                        repo=mock_repo,
                        file_bytes=b"test",
                        file_name=f"data{ext}",
                        source_profile="herdhr",
                        dataset_type="payroll",
                    )
                    assert result.status == UploadStatus.uploaded
