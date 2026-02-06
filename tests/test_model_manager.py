"""Tests for model manager behavior with mocked backends."""

from pathlib import Path
from types import SimpleNamespace
import sys

import pytest
from PIL import Image

import identity_gen.model_manager as mm
from identity_gen.model_config import ModelConfig


class FakeConfigManager:
    def __init__(self, base: Path):
        self.base = base
        self.selected = None
        self.downloaded = set()
        self.models = {
            "tiny-sd": ModelConfig(
                repo_id="repo/tiny",
                name="Tiny",
                description="d",
                size_gb=1.0,
                prompt_template="photo {gender}",
                negative_prompt="bad",
                guidance_scale=7.5,
                num_inference_steps=20,
            )
        }

    def get_selected_model(self):
        if self.selected is None:
            return None
        return self.selected, self.models[self.selected]

    def is_model_downloaded(self, model_key: str) -> bool:
        return model_key in self.downloaded

    def get_model_config(self, model_key: str):
        return self.models.get(model_key)

    def get_model_dir(self, model_key: str) -> Path:
        return self.base / model_key

    def get_cache_dir(self) -> Path:
        return self.base


@pytest.fixture
def fake_manager(tmp_path, monkeypatch):
    cfg = FakeConfigManager(tmp_path)
    monkeypatch.setattr(mm, "get_config_manager", lambda: cfg)
    manager = mm.ModelManager()
    mm._pipeline_cache.clear()
    return manager, cfg


def test_is_model_available_uses_selected_model(fake_manager):
    manager, cfg = fake_manager
    assert manager.is_model_available() is False

    cfg.selected = "tiny-sd"
    assert manager.is_model_available() is False

    cfg.downloaded.add("tiny-sd")
    assert manager.is_model_available() is True


def test_download_model_unknown_returns_false(fake_manager):
    manager, _ = fake_manager
    assert manager.download_model("missing") is False


def test_download_model_success(fake_manager, monkeypatch):
    manager, cfg = fake_manager
    calls = {}

    def fake_snapshot_download(repo_id: str, local_dir: str):
        calls["repo_id"] = repo_id
        calls["local_dir"] = local_dir

    monkeypatch.setitem(
        sys.modules,
        "huggingface_hub",
        SimpleNamespace(snapshot_download=fake_snapshot_download),
    )

    assert manager.download_model("tiny-sd") is True
    assert calls["repo_id"] == "repo/tiny"
    assert calls["local_dir"].endswith("tiny-sd")
    cfg.downloaded.add("tiny-sd")


def test_download_model_importerror(fake_manager, monkeypatch):
    manager, _ = fake_manager

    orig_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "huggingface_hub":
            raise ImportError("missing")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)
    assert manager.download_model("tiny-sd") is False


def test_download_model_exception_returns_false(fake_manager, monkeypatch):
    manager, _ = fake_manager

    def bad_snapshot_download(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setitem(
        sys.modules,
        "huggingface_hub",
        SimpleNamespace(snapshot_download=bad_snapshot_download),
    )
    assert manager.download_model("tiny-sd") is False


def test_load_pipeline_no_selected_returns_none(fake_manager):
    manager, _ = fake_manager
    assert manager.load_pipeline() is None


def test_load_pipeline_uses_selected_tuple_branch(fake_manager, monkeypatch):
    manager, cfg = fake_manager
    cfg.selected = "tiny-sd"
    cfg.downloaded.add("tiny-sd")

    class P:
        @classmethod
        def from_pretrained(cls, *_a, **_k):
            return cls()

        def to(self, _d):
            return self

    monkeypatch.setitem(
        sys.modules,
        "torch",
        SimpleNamespace(
            float16="f16",
            float32="f32",
            cuda=SimpleNamespace(is_available=lambda: True),
            backends=SimpleNamespace(mps=SimpleNamespace(is_available=lambda: False)),
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "diffusers.pipelines.stable_diffusion.pipeline_stable_diffusion",
        SimpleNamespace(StableDiffusionPipeline=P),
    )
    assert manager.load_pipeline() is not None


def test_load_pipeline_uses_cache(fake_manager):
    manager, _ = fake_manager
    mm._pipeline_cache["tiny-sd"] = object()
    assert manager.load_pipeline("tiny-sd") is mm._pipeline_cache["tiny-sd"]


def test_load_pipeline_not_downloaded_returns_none(fake_manager):
    manager, _ = fake_manager
    assert manager.load_pipeline("tiny-sd") is None


def test_load_pipeline_success_cpu_path(fake_manager, monkeypatch):
    manager, cfg = fake_manager
    cfg.downloaded.add("tiny-sd")
    (cfg.get_model_dir("tiny-sd") / "model_index.json").parent.mkdir(
        parents=True, exist_ok=True
    )
    (cfg.get_model_dir("tiny-sd") / "model_index.json").write_text(
        "{}", encoding="utf-8"
    )

    class FakePipeline:
        def __init__(self):
            self.device = "cpu"
            self.attn = False
            self.offload = False

        @classmethod
        def from_pretrained(cls, *_args, **_kwargs):
            return cls()

        def to(self, device: str):
            self.device = device
            return self

        def enable_attention_slicing(self):
            self.attn = True

        def enable_sequential_cpu_offload(self):
            self.offload = True

    fake_torch = SimpleNamespace(
        float16="f16",
        float32="f32",
        cuda=SimpleNamespace(is_available=lambda: False),
        backends=SimpleNamespace(mps=SimpleNamespace(is_available=lambda: False)),
    )

    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setitem(
        sys.modules,
        "diffusers.pipelines.stable_diffusion.pipeline_stable_diffusion",
        SimpleNamespace(StableDiffusionPipeline=FakePipeline),
    )

    pipe = manager.load_pipeline("tiny-sd")
    assert pipe is not None
    assert pipe.device == "cpu"
    assert pipe.attn is True
    assert pipe.offload is True


def test_load_pipeline_unknown_model(fake_manager):
    manager, _ = fake_manager
    assert manager.load_pipeline("missing") is None


def test_load_pipeline_importerror_branch(fake_manager, monkeypatch):
    manager, cfg = fake_manager
    cfg.downloaded.add("tiny-sd")

    orig_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "torch":
            raise ImportError("missing")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)
    assert manager.load_pipeline("tiny-sd") is None


def test_load_pipeline_mps_auto_and_alt_load_fallback(fake_manager, monkeypatch):
    manager, cfg = fake_manager
    cfg.downloaded.add("tiny-sd")
    cache_dir = cfg.get_model_dir("tiny-sd")
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "model_index.json").write_text("{}", encoding="utf-8")

    class FakePipeline:
        def __init__(self):
            self.device = "cpu"

        @classmethod
        def from_pretrained(cls, *_args, **kwargs):
            if "local_files_only" not in kwargs:
                raise RuntimeError("super __getattr__")
            return cls()

        def to(self, device: str):
            self.device = device
            return self

        def enable_attention_slicing(self):
            return None

    fake_torch = SimpleNamespace(
        float16="f16",
        float32="f32",
        cuda=SimpleNamespace(is_available=lambda: False),
        backends=SimpleNamespace(mps=SimpleNamespace(is_available=lambda: True)),
    )
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setitem(
        sys.modules,
        "diffusers.pipelines.stable_diffusion.pipeline_stable_diffusion",
        SimpleNamespace(StableDiffusionPipeline=FakePipeline),
    )

    pipe = manager.load_pipeline("tiny-sd")
    assert pipe is not None
    assert pipe.device == "cpu"


def test_load_pipeline_general_exception(fake_manager, monkeypatch):
    manager, cfg = fake_manager
    cfg.downloaded.add("tiny-sd")

    class BadPipeline:
        @classmethod
        def from_pretrained(cls, *_args, **_kwargs):
            raise RuntimeError("boom")

    fake_torch = SimpleNamespace(
        float16="f16",
        float32="f32",
        cuda=SimpleNamespace(is_available=lambda: False),
        backends=SimpleNamespace(mps=SimpleNamespace(is_available=lambda: False)),
    )
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setitem(
        sys.modules,
        "diffusers.pipelines.stable_diffusion.pipeline_stable_diffusion",
        SimpleNamespace(StableDiffusionPipeline=BadPipeline),
    )
    assert manager.load_pipeline("tiny-sd") is None


def test_load_pipeline_alt_load_both_fail(fake_manager, monkeypatch):
    manager, cfg = fake_manager
    cfg.downloaded.add("tiny-sd")
    cache = cfg.get_model_dir("tiny-sd")
    cache.mkdir(parents=True, exist_ok=True)
    (cache / "model_index.json").write_text("{}", encoding="utf-8")

    class P:
        @classmethod
        def from_pretrained(cls, *_a, **_k):
            raise RuntimeError("super __getattr__")

    monkeypatch.setitem(
        sys.modules,
        "torch",
        SimpleNamespace(
            float16="f16",
            float32="f32",
            cuda=SimpleNamespace(is_available=lambda: False),
            backends=SimpleNamespace(mps=SimpleNamespace(is_available=lambda: False)),
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "diffusers.pipelines.stable_diffusion.pipeline_stable_diffusion",
        SimpleNamespace(StableDiffusionPipeline=P),
    )
    assert manager.load_pipeline("tiny-sd") is None


def test_load_pipeline_alt_branch_raises_when_no_local_model(fake_manager, monkeypatch):
    manager, cfg = fake_manager
    cfg.downloaded.add("tiny-sd")
    cache = cfg.get_model_dir("tiny-sd")
    cache.mkdir(parents=True, exist_ok=True)

    class P:
        @classmethod
        def from_pretrained(cls, *_a, **_k):
            raise RuntimeError("super __getattr__")

    monkeypatch.setitem(
        sys.modules,
        "torch",
        SimpleNamespace(
            float16="f16",
            float32="f32",
            cuda=SimpleNamespace(is_available=lambda: False),
            backends=SimpleNamespace(mps=SimpleNamespace(is_available=lambda: False)),
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "diffusers.pipelines.stable_diffusion.pipeline_stable_diffusion",
        SimpleNamespace(StableDiffusionPipeline=P),
    )
    assert manager.load_pipeline("tiny-sd") is None


def test_generate_image_returns_first_image(fake_manager, monkeypatch):
    manager, _ = fake_manager
    img = Image.new("RGB", (32, 32), (255, 255, 255))

    class FakePipeline:
        device = "cpu"

        def __call__(self, **_kwargs):
            return SimpleNamespace(images=[img])

    monkeypatch.setattr(manager, "load_pipeline", lambda _=None: FakePipeline())
    monkeypatch.setitem(
        sys.modules,
        "torch",
        SimpleNamespace(
            Generator=lambda device="cpu": SimpleNamespace(
                manual_seed=lambda _: object()
            )
        ),
    )

    out = manager.generate_image(prompt="x", seed=123)
    assert out is img


def test_generate_image_generator_runtimeerror_fallback_cpu(fake_manager, monkeypatch):
    manager, _ = fake_manager
    image = Image.new("RGB", (5, 5), (255, 255, 255))

    class FakePipeline:
        device = "meta"

        def __call__(self, **_kwargs):
            return SimpleNamespace(images=[image])

    class _Gen:
        def __init__(self, device="cpu"):
            self.device = device

        def manual_seed(self, _seed):
            if self.device != "cpu":
                raise RuntimeError("bad device")
            return object()

    monkeypatch.setattr(manager, "load_pipeline", lambda _=None: FakePipeline())
    monkeypatch.setitem(
        sys.modules,
        "torch",
        SimpleNamespace(Generator=lambda device="cpu": _Gen(device)),
    )
    out = manager.generate_image(prompt="x", seed=1)
    assert out is image


def test_generate_image_pipeline_none(fake_manager, monkeypatch):
    manager, _ = fake_manager
    monkeypatch.setattr(manager, "load_pipeline", lambda _=None: None)
    assert manager.generate_image(prompt="x") is None


def test_generate_image_generator_runtimeerror_on_non_meta_device(
    fake_manager, monkeypatch
):
    manager, _ = fake_manager
    image = Image.new("RGB", (4, 4), (255, 255, 255))

    class Pipe:
        device = "cuda"

        def __call__(self, **_k):
            return SimpleNamespace(images=[image])

    class G:
        def __init__(self, device="cpu"):
            self.device = device

        def manual_seed(self, _):
            if self.device == "cuda":
                raise RuntimeError("x")
            return object()

    monkeypatch.setattr(manager, "load_pipeline", lambda _=None: Pipe())
    monkeypatch.setitem(
        sys.modules, "torch", SimpleNamespace(Generator=lambda device="cpu": G(device))
    )
    assert manager.generate_image(prompt="x", seed=7) is image


def test_generate_image_handles_pipeline_failure(fake_manager, monkeypatch):
    manager, _ = fake_manager

    class BrokenPipeline:
        device = "cpu"

        def __call__(self, **_kwargs):
            raise RuntimeError("bad")

    monkeypatch.setattr(manager, "load_pipeline", lambda _=None: BrokenPipeline())
    monkeypatch.setitem(
        sys.modules,
        "torch",
        SimpleNamespace(
            Generator=lambda device="cpu": SimpleNamespace(
                manual_seed=lambda _: object()
            )
        ),
    )
    assert manager.generate_image(prompt="x") is None


def test_clear_cache(fake_manager):
    manager, _ = fake_manager
    mm._pipeline_cache["x"] = object()
    manager.clear_cache()
    assert mm._pipeline_cache == {}


def test_delete_model_success_and_missing(fake_manager):
    manager, cfg = fake_manager
    assert manager.delete_model("tiny-sd") is False

    model_dir = cfg.get_model_dir("tiny-sd")
    model_dir.mkdir(parents=True)
    (model_dir / "a.txt").write_text("x", encoding="utf-8")
    mm._pipeline_cache["tiny-sd"] = object()

    assert manager.delete_model("tiny-sd") is True
    assert not model_dir.exists()
    assert "tiny-sd" not in mm._pipeline_cache


def test_delete_model_exception(fake_manager, monkeypatch):
    manager, cfg = fake_manager
    model_dir = cfg.get_model_dir("tiny-sd")
    model_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setitem(
        sys.modules,
        "shutil",
        SimpleNamespace(rmtree=lambda *_: (_ for _ in ()).throw(OSError("x"))),
    )
    assert manager.delete_model("tiny-sd") is False


def test_get_model_info(fake_manager):
    manager, cfg = fake_manager
    assert manager.get_model_info("missing") is None

    cfg.downloaded.add("tiny-sd")
    model_dir = cfg.get_model_dir("tiny-sd")
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / "x.bin").write_bytes(b"abc")
    info = manager.get_model_info("tiny-sd")
    assert info is not None
    assert info["key"] == "tiny-sd"
    assert info["is_downloaded"] is True


def test_get_model_info_size_calc_exception(fake_manager, monkeypatch):
    manager, cfg = fake_manager
    cfg.downloaded.add("tiny-sd")
    model_dir = cfg.get_model_dir("tiny-sd")
    model_dir.mkdir(parents=True, exist_ok=True)

    class _Bad:
        def rglob(self, _):
            raise OSError("bad")

        def exists(self):
            return True

        def __str__(self):
            return "bad"

    monkeypatch.setattr(cfg, "get_model_dir", lambda _k: _Bad())
    info = manager.get_model_info("tiny-sd")
    assert info is not None
    assert info["actual_size_mb"] == 0


def test_get_model_manager_singleton(monkeypatch):
    fake = object()
    mm._model_manager = None
    monkeypatch.setattr(mm, "ModelManager", lambda: fake)
    assert mm.get_model_manager() is fake
    assert mm.get_model_manager() is fake
