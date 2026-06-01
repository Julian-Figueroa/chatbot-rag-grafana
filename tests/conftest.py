from unittest.mock import MagicMock, patch
import pytest


@pytest.fixture(scope="session", autouse=True)
def mock_cross_encoder_model():
    """Prevent sentence-transformers from downloading/loading the cross-encoder model during tests."""
    mock_instance = MagicMock()
    mock_instance.predict.return_value = []
    with patch("sentence_transformers.CrossEncoder", return_value=mock_instance):
        yield
