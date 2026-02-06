"""Tests for model configuration manager."""

import json

from identity_gen.model_config import (
    DEFAULT_MODELS,
    ModelConfig,
    ModelConfigManager,
)
import identity_gen.model_config as mc


def test_model_config_format_prompt_gender_mapping() -> None:
    config = ModelConfig(
        repo_id="repo/x",
        name="x",
        description="d",
        size_gb=1.0,
        prompt_template="photo of {gender}",
        negative_prompt="",
        guidance_scale=7.5,
        num_inference_steps=20,
    )

    assert config.format_prompt("male") == "photo of man"
    assert config.format_prompt("female") == "photo of woman"
    assert config.format_prompt("other") == "photo of person"


def test_config_manager_loads_defaults_when_missing(tmp_path) -> None:
    manager = ModelConfigManager(config_dir=tmp_path)
    assert manager.get_selected_model() is None
    assert manager._config["custom_models"] == {}
    assert manager.get_cache_dir().exists()


def test_config_manager_recovers_from_invalid_json(tmp_path) -> None:
    config_file = tmp_path / "model_config.json"
    config_file.write_text("{invalid-json", encoding="utf-8")
    manager = ModelConfigManager(config_dir=tmp_path)
    assert manager._config["selected_model"] is None


def test_get_model_dir_normalizes_repo_key(tmp_path) -> None:
    manager = ModelConfigManager(config_dir=tmp_path)
    assert manager.get_model_dir("foo/bar").name == "foo--bar"


def test_is_model_downloaded_checks_essential_files(tmp_path) -> None:
    manager = ModelConfigManager(config_dir=tmp_path)
    model_dir = manager.get_model_dir("tiny-sd")
    assert manager.is_model_downloaded("tiny-sd") is False

    (model_dir / "model_index.json").parent.mkdir(parents=True, exist_ok=True)
    (model_dir / "model_index.json").write_text("{}", encoding="utf-8")
    (model_dir / "unet").mkdir(parents=True, exist_ok=True)
    (model_dir / "unet" / "diffusion_pytorch_model.bin").write_text(
        "x", encoding="utf-8"
    )
    assert manager.is_model_downloaded("tiny-sd") is False

    (model_dir / "text_encoder").mkdir(parents=True, exist_ok=True)
    (model_dir / "text_encoder" / "model.safetensors").write_text("x", encoding="utf-8")
    assert manager.is_model_downloaded("tiny-sd") is True


def test_get_model_config_for_default_custom_and_missing(tmp_path) -> None:
    manager = ModelConfigManager(config_dir=tmp_path)

    default_cfg = manager.get_model_config("tiny-sd")
    assert default_cfg is not None
    assert default_cfg.custom is False

    added = manager.add_custom_model(
        key="my-model",
        repo_id="org/model",
        name="My Model",
        description="custom",
        size_gb=2.0,
        prompt_template="photo {gender}",
    )
    assert added is True

    custom_cfg = manager.get_model_config("my-model")
    assert custom_cfg is not None
    assert custom_cfg.custom is True
    assert manager.get_model_config("missing") is None


def test_list_available_models_contains_default_and_custom(tmp_path) -> None:
    manager = ModelConfigManager(config_dir=tmp_path)
    manager.add_custom_model(
        key="my-model",
        repo_id="org/model",
        name="My Model",
        description="custom",
        size_gb=2.0,
        prompt_template="photo {gender}",
    )

    models = manager.list_available_models()
    assert "tiny-sd" in models
    assert "my-model" in models


def test_selected_model_set_get_and_invalid(tmp_path) -> None:
    manager = ModelConfigManager(config_dir=tmp_path)
    assert manager.set_selected_model("missing") is False
    assert manager.set_selected_model("tiny-sd") is True

    selected = manager.get_selected_model()
    assert selected is not None
    assert selected[0] == "tiny-sd"


def test_selected_model_returns_none_if_config_deleted(tmp_path) -> None:
    manager = ModelConfigManager(config_dir=tmp_path)
    manager._config["selected_model"] = "unknown"
    assert manager.get_selected_model() is None


def test_add_custom_model_cannot_override_default(tmp_path) -> None:
    manager = ModelConfigManager(config_dir=tmp_path)
    ok = manager.add_custom_model(
        key="tiny-sd",
        repo_id="org/model",
        name="Bad",
        description="bad",
        size_gb=1.0,
        prompt_template="x {gender}",
    )
    assert ok is False


def test_remove_custom_model_and_reset_selected(tmp_path) -> None:
    manager = ModelConfigManager(config_dir=tmp_path)
    manager.add_custom_model(
        key="my-model",
        repo_id="org/model",
        name="My Model",
        description="custom",
        size_gb=2.0,
        prompt_template="photo {gender}",
    )
    manager.set_selected_model("my-model")
    assert manager.remove_custom_model("my-model") is True
    assert manager._config["selected_model"] is None
    assert manager.remove_custom_model("my-model") is False


def test_is_configured_depends_on_download_status(tmp_path, monkeypatch) -> None:
    manager = ModelConfigManager(config_dir=tmp_path)
    manager.set_selected_model("tiny-sd")

    monkeypatch.setattr(manager, "is_model_downloaded", lambda _: False)
    assert manager.is_configured() is False

    monkeypatch.setattr(manager, "is_model_downloaded", lambda _: True)
    assert manager.is_configured() is True


def test_reset_configuration_clears_selection(tmp_path) -> None:
    manager = ModelConfigManager(config_dir=tmp_path)
    manager.set_selected_model("tiny-sd")
    manager.reset_configuration()
    assert manager.get_selected_model() is None


def test_save_and_reload_config_file(tmp_path) -> None:
    manager = ModelConfigManager(config_dir=tmp_path)
    manager.set_selected_model("tiny-sd")
    manager.add_custom_model(
        key="my-model",
        repo_id="org/model",
        name="My Model",
        description="custom",
        size_gb=2.0,
        prompt_template="photo {gender}",
    )

    raw = json.loads((tmp_path / "model_config.json").read_text(encoding="utf-8"))
    assert raw["selected_model"] == "tiny-sd"
    assert "my-model" in raw["custom_models"]


def test_default_models_have_expected_keys() -> None:
    assert {"tiny-sd", "small-sd", "realistic-vision"}.issubset(DEFAULT_MODELS.keys())


def test_init_without_config_dir_branch(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(mc.Path, "home", lambda: tmp_path)
    manager = ModelConfigManager()
    assert manager.config_dir == tmp_path / ".identity_gen"


def test_save_config_exception_branch(tmp_path, monkeypatch) -> None:
    manager = ModelConfigManager(config_dir=tmp_path)

    def bad_open(*_args, **_kwargs):
        raise OSError("nope")

    monkeypatch.setattr("builtins.open", bad_open)
    manager.reset_configuration()


def test_set_selected_model_returns_false_when_save_fails(
    tmp_path, monkeypatch
) -> None:
    manager = ModelConfigManager(config_dir=tmp_path)

    def bad_open(*_args, **_kwargs):
        raise OSError("nope")

    monkeypatch.setattr("builtins.open", bad_open)
    assert manager.set_selected_model("tiny-sd") is False


def test_get_config_manager_singleton(monkeypatch, tmp_path) -> None:
    mc._config_manager = None
    monkeypatch.setattr(mc.Path, "home", lambda: tmp_path)
    first = mc.get_config_manager()
    second = mc.get_config_manager()
    assert first is second


def test_is_model_downloaded_existing_dir_but_missing_files(tmp_path) -> None:
    manager = ModelConfigManager(config_dir=tmp_path)
    model_dir = manager.get_model_dir("tiny-sd")
    model_dir.mkdir(parents=True, exist_ok=True)
    assert manager.is_model_downloaded("tiny-sd") is False


def test_is_configured_without_selected(tmp_path) -> None:
    manager = ModelConfigManager(config_dir=tmp_path)
    assert manager.is_configured() is False
