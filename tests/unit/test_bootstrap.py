import pytest

from fly_brain.bootstrap import configure_mlx

pytestmark = pytest.mark.unit


def test_bootstrap_sets_safe_precision_before_backend_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv('MLX_ENABLE_TF32', raising=False)
    assert configure_mlx() == '0'


def test_bootstrap_rejects_explicit_unsafe_precision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv('MLX_ENABLE_TF32', '1')
    with pytest.raises(RuntimeError, match='MLX_ENABLE_TF32=0'):
        configure_mlx()
