"""Tests for CLI model-management and generate-idcard branches."""

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from click.testing import CliRunner

import identity_gen.cli as cli_module
from identity_gen.cli import (
    _prompt_avatar_backend,
    cli,
    detect_format_from_extension,
    generate_default_filename,
)


@dataclass
class _Cfg:
    name: str = "Tiny"
    repo_id: str = "repo/tiny"
    size_gb: float = 1.0


class _FakeConfigManager:
    def __init__(self, downloaded=None, selected=None):
        self._downloaded = set(downloaded or [])
        self._selected = selected

    def get_selected_model(self):
        if not self._selected:
            return None
        return self._selected, _Cfg(name="Tiny", repo_id="repo/tiny", size_gb=1.0)

    def is_model_downloaded(self, key):
        return key in self._downloaded

    def list_available_models(self):
        return {"tiny-sd": _Cfg(), "small-sd": _Cfg(name="Small")}

    def get_model_config(self, key):
        if key == "tiny-sd":
            return _Cfg()
        if key == "small-sd":
            return _Cfg(name="Small", repo_id="repo/small", size_gb=1.5)
        return None

    def set_selected_model(self, key):
        self._selected = key
        return True

    def get_cache_dir(self):
        return Path("/tmp/model-cache")


class _FakeModelManager:
    def __init__(self, download_ok=True, delete_ok=True):
        self.download_ok = download_ok
        self.delete_ok = delete_ok
        self.download_calls = []
        self.delete_calls = []

    def download_model(self, key):
        self.download_calls.append(key)
        return self.download_ok

    def delete_model(self, key):
        self.delete_calls.append(key)
        return self.delete_ok

    def get_model_info(self, _key):
        return {"actual_size_mb": 1024}


def test_cli_model_list_and_status(monkeypatch) -> None:
    cfg = _FakeConfigManager(downloaded={"tiny-sd"}, selected="tiny-sd")
    mgr = _FakeModelManager()

    monkeypatch.setattr("identity_gen.model_config.get_config_manager", lambda: cfg)
    monkeypatch.setattr("identity_gen.model_manager.get_model_manager", lambda: mgr)

    runner = CliRunner()
    r1 = runner.invoke(cli, ["model", "list"])
    assert r1.exit_code == 0
    assert "tiny-sd" in r1.output

    r2 = runner.invoke(cli, ["model", "status"])
    assert r2.exit_code == 0
    assert "Model Configuration Status" in r2.output


def test_cli_model_configure_download_and_select(monkeypatch) -> None:
    cfg = _FakeConfigManager(downloaded=set(), selected=None)
    mgr = _FakeModelManager(download_ok=True)

    monkeypatch.setattr("identity_gen.model_config.get_config_manager", lambda: cfg)
    monkeypatch.setattr("identity_gen.model_manager.get_model_manager", lambda: mgr)

    inputs = iter(["1", "y"])
    monkeypatch.setattr("builtins.input", lambda *_: next(inputs))

    runner = CliRunner()
    result = runner.invoke(cli, ["model", "configure"])
    assert result.exit_code == 0
    assert cfg._selected == "tiny-sd"
    assert mgr.download_calls == ["tiny-sd"]


def test_cli_model_download_and_delete(monkeypatch) -> None:
    cfg = _FakeConfigManager(downloaded={"tiny-sd"}, selected="tiny-sd")
    mgr = _FakeModelManager(download_ok=True, delete_ok=True)

    monkeypatch.setattr("identity_gen.model_config.get_config_manager", lambda: cfg)
    monkeypatch.setattr("identity_gen.model_manager.get_model_manager", lambda: mgr)
    monkeypatch.setattr("builtins.input", lambda *_: "y")

    runner = CliRunner()
    # 已下载分支
    r1 = runner.invoke(cli, ["model", "download", "tiny-sd"])
    assert r1.exit_code == 0

    # 删除分支
    r2 = runner.invoke(cli, ["model", "delete", "tiny-sd"])
    assert r2.exit_code == 0
    assert mgr.delete_calls == ["tiny-sd"]


def test_cli_generate_idcard_command(monkeypatch, tmp_path) -> None:
    generated = {}

    class _FakeIdentityGenerator:
        def __init__(self, _config):
            pass

        def generate_batch(self):
            return [SimpleNamespace(name="张三", ssn="1101")]

    class _FakeIDCardGen:
        def generate_batch(self, **kwargs):
            generated.update(kwargs)
            out = Path(kwargs["output_dir"]) / "a.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(b"x")
            return [out]

    monkeypatch.setattr(
        "identity_gen.cli._prompt_avatar_backend", lambda: ("fallback", True)
    )
    monkeypatch.setattr("identity_gen.cli.IdentityGenerator", _FakeIdentityGenerator)
    monkeypatch.setattr("identity_gen.cli.IDCardImageGenerator", _FakeIDCardGen)

    runner = CliRunner()
    out_dir = tmp_path / "ids"
    res = runner.invoke(
        cli, ["generate-idcard", "--count", "1", "--output-dir", str(out_dir)]
    )
    assert res.exit_code == 0
    assert generated["include_avatar"] is True
    assert generated["avatar_backend"] == "fallback"


def test_prompt_avatar_backend_branches(monkeypatch) -> None:
    monkeypatch.setattr(cli_module.sys.stdin, "isatty", lambda: False)
    assert _prompt_avatar_backend() == ("auto", True)

    monkeypatch.setattr(cli_module.sys.stdin, "isatty", lambda: True)
    for choice, expected in {
        "1": ("diffusers", True),
        "2": ("ark", True),
        "3": ("random_face", True),
        "4": ("fallback", True),
        "5": ("auto", False),
    }.items():
        monkeypatch.setattr("click.prompt", lambda *_a, **_k: choice)
        assert _prompt_avatar_backend() == expected


def test_detect_format_and_default_filename() -> None:
    assert detect_format_from_extension("a.unknown") is None
    fmt = detect_format_from_extension("a.json")
    assert fmt is not None
    assert fmt.value == "json"
    assert generate_default_filename().endswith(".csv")


def test_cli_main_error_verbose_branch(monkeypatch) -> None:
    class _BadGen:
        def __init__(self, _cfg):
            pass

        def generate_batch(self):
            raise RuntimeError("boom")

    monkeypatch.setattr("identity_gen.cli.IdentityGenerator", _BadGen)
    runner = CliRunner()
    res = runner.invoke(cli, ["--verbose", "--stdout"])
    assert res.exit_code != 0


def test_cli_generation_size_and_idcard_more_than_five(monkeypatch, tmp_path) -> None:
    class _Gen:
        def __init__(self, _cfg):
            pass

        def generate_batch(self):
            return [SimpleNamespace(to_dict=lambda fields=None: {"name": "张三"})]

    class _Fmt:
        def format(self, *_args, **_kwargs):
            return "x"

        def write_output(self, _content, output_path):
            Path(output_path).write_text("x", encoding="utf-8")

    class _ID:
        def generate_batch(self, **kwargs):
            out_dir = Path(kwargs["output_dir"])
            out_dir.mkdir(parents=True, exist_ok=True)
            files = []
            for i in range(6):
                p = out_dir / f"{i}.png"
                p.write_bytes(b"x")
                files.append(p)
            return files

    monkeypatch.setattr("identity_gen.cli.IdentityGenerator", _Gen)
    monkeypatch.setattr("identity_gen.cli.IdentityFormatter", lambda: _Fmt())
    monkeypatch.setattr("identity_gen.cli.IDCardImageGenerator", _ID)
    monkeypatch.setattr(
        "identity_gen.cli._prompt_avatar_backend", lambda: ("fallback", True)
    )
    monkeypatch.setattr("os.path.getsize", lambda *_: 2 * 1024 * 1024)

    out = tmp_path / "x.badext"
    runner = CliRunner()
    res = runner.invoke(
        cli, ["--output", str(out), "--idcard", "--idcard-dir", str(tmp_path / "ids")]
    )
    assert res.exit_code == 0


def test_cli_generate_idcard_no_avatar_and_error(monkeypatch, tmp_path) -> None:
    class _Gen:
        def __init__(self, _cfg):
            pass

        def generate_batch(self):
            return []

    class _BadID:
        def generate_batch(self, **_kwargs):
            raise RuntimeError("bad")

    monkeypatch.setattr("identity_gen.cli.IdentityGenerator", _Gen)
    monkeypatch.setattr("identity_gen.cli.IDCardImageGenerator", _BadID)
    runner = CliRunner()
    ok = runner.invoke(
        cli, ["generate-idcard", "--no-avatar", "--output-dir", str(tmp_path / "a")]
    )
    assert ok.exit_code != 0


def test_cli_model_command_error_branches(monkeypatch) -> None:
    runner = CliRunner()

    # model list exception
    monkeypatch.setattr(
        "identity_gen.model_config.get_config_manager",
        lambda: (_ for _ in ()).throw(RuntimeError("x")),
    )
    r1 = runner.invoke(cli, ["model", "list"])
    assert r1.exit_code != 0


def test_cli_model_configure_more_branches(monkeypatch) -> None:
    cfg = _FakeConfigManager(downloaded=set(), selected=None)
    mgr = _FakeModelManager(download_ok=False)
    monkeypatch.setattr("identity_gen.model_config.get_config_manager", lambda: cfg)
    monkeypatch.setattr("identity_gen.model_manager.get_model_manager", lambda: mgr)

    # valueerror + invalid index + quit
    inputs = iter(["abc", "9", "q"])
    monkeypatch.setattr("builtins.input", lambda *_: next(inputs))
    runner = CliRunner()
    r = runner.invoke(cli, ["model", "configure"])
    assert r.exit_code == 0

    # download fail branch
    inputs2 = iter(["1", "y"])
    monkeypatch.setattr("builtins.input", lambda *_: next(inputs2))
    r2 = runner.invoke(cli, ["model", "configure"])
    assert r2.exit_code == 0

    # keyboardinterrupt branch
    monkeypatch.setattr(
        "builtins.input", lambda *_: (_ for _ in ()).throw(KeyboardInterrupt())
    )
    r3 = runner.invoke(cli, ["model", "configure"])
    assert r3.exit_code == 0


def test_cli_model_download_delete_status_branches(monkeypatch) -> None:
    runner = CliRunner()

    cfg = _FakeConfigManager(downloaded=set(), selected=None)
    mgr = _FakeModelManager(download_ok=False, delete_ok=False)
    monkeypatch.setattr("identity_gen.model_config.get_config_manager", lambda: cfg)
    monkeypatch.setattr("identity_gen.model_manager.get_model_manager", lambda: mgr)

    # unknown model
    r1 = runner.invoke(cli, ["model", "download", "unknown"])
    assert r1.exit_code != 0

    # model exists but config None
    monkeypatch.setattr(cfg, "list_available_models", lambda: {"tiny-sd": _Cfg()})
    monkeypatch.setattr(cfg, "get_model_config", lambda _k: None)
    r2 = runner.invoke(cli, ["model", "download", "tiny-sd"])
    assert r2.exit_code != 0

    # delete not downloaded
    monkeypatch.setattr(cfg, "is_model_downloaded", lambda _k: False)
    r3 = runner.invoke(cli, ["model", "delete", "tiny-sd"])
    assert r3.exit_code == 0

    # delete config none
    monkeypatch.setattr(cfg, "is_model_downloaded", lambda _k: True)
    monkeypatch.setattr(cfg, "get_model_config", lambda _k: None)
    r4 = runner.invoke(cli, ["model", "delete", "tiny-sd", "--force"])
    assert r4.exit_code != 0

    # delete cancel
    monkeypatch.setattr(cfg, "get_model_config", lambda _k: _Cfg())
    monkeypatch.setattr("builtins.input", lambda *_: "n")
    r5 = runner.invoke(cli, ["model", "delete", "tiny-sd"])
    assert r5.exit_code == 0

    # delete fail
    monkeypatch.setattr("builtins.input", lambda *_: "y")
    r6 = runner.invoke(cli, ["model", "delete", "tiny-sd"])
    assert r6.exit_code != 0

    # status no selected
    monkeypatch.setattr(cfg, "get_selected_model", lambda: None)
    r7 = runner.invoke(cli, ["model", "status"])
    assert r7.exit_code == 0

    # status exception
    monkeypatch.setattr(
        "identity_gen.model_config.get_config_manager",
        lambda: (_ for _ in ()).throw(RuntimeError("e")),
    )
    r8 = runner.invoke(cli, ["model", "status"])
    assert r8.exit_code != 0


def test_cli_remaining_branches(monkeypatch, tmp_path) -> None:
    runner = CliRunner()

    # main command with exclude and no-avatar (cover line 299/310)
    class _Gen:
        def __init__(self, _cfg):
            pass

        def generate_batch(self):
            return [SimpleNamespace(to_dict=lambda fields=None: {"name": "张三"})]

    class _Fmt:
        def format(self, *_a, **_k):
            return "data"

        def write_output(self, content, output_path):
            Path(output_path).write_text(content, encoding="utf-8")

    class _ID:
        def generate_batch(self, **kwargs):
            return [Path(kwargs["output_dir"]) / "a.png"]

    monkeypatch.setattr("identity_gen.cli.IdentityGenerator", _Gen)
    monkeypatch.setattr("identity_gen.cli.IdentityFormatter", lambda: _Fmt())
    monkeypatch.setattr("identity_gen.cli.IDCardImageGenerator", _ID)
    res = runner.invoke(
        cli,
        [
            "--output",
            str(tmp_path / "out.csv"),
            "--exclude",
            "email",
            "--idcard-no-avatar",
        ],
    )
    assert res.exit_code == 0

    # generate-idcard seed line
    monkeypatch.setattr(
        "identity_gen.cli.IdentityGenerator",
        lambda _cfg: SimpleNamespace(generate_batch=lambda: []),
    )
    monkeypatch.setattr(
        "identity_gen.cli.IDCardImageGenerator",
        lambda: SimpleNamespace(generate_batch=lambda **_: []),
    )
    res2 = runner.invoke(
        cli,
        [
            "generate-idcard",
            "--seed",
            "42",
            "--no-avatar",
            "--output-dir",
            str(tmp_path / "id"),
        ],
    )
    assert res2.exit_code == 0

    # model list no selected
    cfg = _FakeConfigManager(downloaded=set(), selected=None)
    mgr = _FakeModelManager()
    monkeypatch.setattr("identity_gen.model_config.get_config_manager", lambda: cfg)
    monkeypatch.setattr("identity_gen.model_manager.get_model_manager", lambda: mgr)
    r1 = runner.invoke(cli, ["model", "list"])
    assert r1.exit_code == 0

    # model configure already downloaded line 692
    cfg2 = _FakeConfigManager(downloaded={"tiny-sd"}, selected=None)
    monkeypatch.setattr("identity_gen.model_config.get_config_manager", lambda: cfg2)
    monkeypatch.setattr("identity_gen.model_manager.get_model_manager", lambda: mgr)
    monkeypatch.setattr("builtins.input", lambda *_: "1")
    r2 = runner.invoke(cli, ["model", "configure"])
    assert r2.exit_code == 0

    # model configure skip download line 720
    cfg3 = _FakeConfigManager(downloaded=set(), selected=None)
    monkeypatch.setattr("identity_gen.model_config.get_config_manager", lambda: cfg3)
    seq = iter(["1", "n"])
    monkeypatch.setattr("builtins.input", lambda *_: next(seq))
    r3 = runner.invoke(cli, ["model", "configure"])
    assert r3.exit_code == 0

    # model configure exception line 736
    monkeypatch.setattr(
        "identity_gen.model_config.get_config_manager",
        lambda: (_ for _ in ()).throw(RuntimeError("x")),
    )
    r4 = runner.invoke(cli, ["model", "configure"])
    assert r4.exit_code != 0

    # model download success/fail/exception
    cfg4 = _FakeConfigManager(downloaded=set(), selected=None)
    monkeypatch.setattr(cfg4, "list_available_models", lambda: {"tiny-sd": _Cfg()})
    monkeypatch.setattr(cfg4, "get_model_config", lambda _k: _Cfg())
    monkeypatch.setattr("identity_gen.model_config.get_config_manager", lambda: cfg4)
    monkeypatch.setattr(
        "identity_gen.model_manager.get_model_manager",
        lambda: _FakeModelManager(download_ok=True),
    )
    r5 = runner.invoke(cli, ["model", "download", "tiny-sd"])
    assert r5.exit_code == 0
    monkeypatch.setattr(
        "identity_gen.model_manager.get_model_manager",
        lambda: _FakeModelManager(download_ok=False),
    )
    r6 = runner.invoke(cli, ["model", "download", "tiny-sd"])
    assert r6.exit_code != 0
    monkeypatch.setattr(
        "identity_gen.model_config.get_config_manager",
        lambda: (_ for _ in ()).throw(RuntimeError("z")),
    )
    r7 = runner.invoke(cli, ["model", "download", "tiny-sd"])
    assert r7.exit_code != 0

    # model delete exception
    cfg5 = _FakeConfigManager(downloaded={"tiny-sd"}, selected=None)
    monkeypatch.setattr(cfg5, "get_model_config", lambda _k: _Cfg())
    monkeypatch.setattr("identity_gen.model_config.get_config_manager", lambda: cfg5)
    monkeypatch.setattr(
        "identity_gen.model_manager.get_model_manager",
        lambda: (_ for _ in ()).throw(RuntimeError("d")),
    )
    r8 = runner.invoke(cli, ["model", "delete", "tiny-sd", "--force"])
    assert r8.exit_code != 0

    # model status not downloaded lines 870-873
    cfg6 = _FakeConfigManager(downloaded=set(), selected="tiny-sd")
    monkeypatch.setattr("identity_gen.model_config.get_config_manager", lambda: cfg6)
    monkeypatch.setattr(
        "identity_gen.model_manager.get_model_manager", lambda: _FakeModelManager()
    )
    r9 = runner.invoke(cli, ["model", "status"])
    assert r9.exit_code == 0


def test_cli_main_entrypoint(monkeypatch) -> None:
    called = {"n": 0}
    monkeypatch.setattr(
        "identity_gen.cli.cli", lambda: called.__setitem__("n", called["n"] + 1)
    )
    cli_module.main()
    assert called["n"] == 1
