"""Tests for local config helpers."""

import importlib


def test_get_ark_config_from_env(monkeypatch) -> None:
    monkeypatch.setenv("ARK_API_KEY", "k1")
    monkeypatch.setenv("ARK_BASE_URL", "https://example.com")
    monkeypatch.setenv("ARK_MODEL_ID", "m1")
    monkeypatch.setenv("ARK_TIMEOUT_SECONDS", "30")

    import identity_gen.config as cfg

    cfg = importlib.reload(cfg)
    ark = cfg.get_ark_config()
    assert ark.api_key == "k1"
    assert ark.base_url == "https://example.com"
    assert ark.model_id == "m1"
    assert ark.timeout_seconds == 30
