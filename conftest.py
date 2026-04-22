# pytest configuration
import pytest


def pytest_configure(config):
    """Registra marcadores personalizados para evitar warnings de pytest."""
    config.addinivalue_line(
        "markers",
        "slow: tests que cargan el modelo GLiNER real (requieren descarga/caché).",
    )
