"""Tests for ID card generation helpers and avatar backends."""

import base64
import io
import sys
from datetime import date
from types import SimpleNamespace

from PIL import Image, ImageDraw, ImageFont
import pytest
import identity_gen.idcard_image_generator as ig

from identity_gen.models import Identity
from identity_gen.idcard_image_generator import (
    AvatarGenerator,
    IDCardImageGenerator,
    _age_bucket,
    _build_id_photo_prompt,
    _calculate_age,
    _decode_base64_image,
    _extract_ark_image,
    _gender_key,
    _generate_ark_face,
    _generate_diffusers_face,
    _interactive_model_setup,
    _is_ark_configured,
    _smart_resize,
    generate_idcard_image,
)


class TestIDCardImageGenerator:
    """Tests for address rendering behavior on ID cards."""

    def test_split_address_lines_uses_two_lines_for_typical_long_address(self):
        generator = IDCardImageGenerator()
        image = Image.new("RGB", (3000, 2000), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        font = generator._get_font("normal")

        address = "山东省青岛市莱西市中山东路162号12单元1630室"
        lines = generator._split_address_lines(
            draw=draw,
            address=address,
            font=font,
            max_width=820,
            max_lines=2,
        )

        assert len(lines) == 2
        assert "".join(lines) == address
        assert draw.textlength(lines[0], font=font) <= 820
        assert draw.textlength(lines[1], font=font) <= 820


class TestAvatarGenerator:
    """Tests for avatar normalization behavior."""

    def test_normalize_avatar_composition_returns_consistent_canvas(self):
        target_size = (500, 670)
        image = Image.new("RGBA", target_size, (255, 255, 255, 0))

        draw = ImageDraw.Draw(image)
        draw.rectangle((200, 260, 320, 660), fill=(30, 30, 30, 255))

        normalized = AvatarGenerator._normalize_avatar_composition(image, target_size)

        assert normalized.size == target_size
        alpha_bbox = normalized.getchannel("A").getbbox()
        assert alpha_bbox is not None
        assert alpha_bbox[1] <= int(target_size[1] * 0.08)


def test_smart_resize_returns_expected_size() -> None:
    src = Image.new("RGB", (1200, 800), (255, 0, 0))
    out = _smart_resize(src, (500, 670))
    assert out.size == (500, 670)


def test_age_related_helpers() -> None:
    assert _calculate_age(None) is None
    assert _age_bucket(None) == "adult"
    assert _age_bucket(10) == "child"
    assert _age_bucket(16) == "teen"
    assert _age_bucket(25) == "young_adult"
    assert _age_bucket(40) == "adult"
    assert _age_bucket(70) == "senior"


def test_gender_key_mapping() -> None:
    assert _gender_key("male") == "male"
    assert _gender_key("girl") == "female"
    assert _gender_key("unknown") == "unknown"
    assert _gender_key(None) == "unknown"


def test_build_id_photo_prompt_contains_attributes() -> None:
    identity = Identity.model_validate({"height": 175, "weight": 68})
    prompt = _build_id_photo_prompt("male", date(2000, 1, 1), identity=identity)
    assert "身高约175厘米" in prompt
    assert "体重约68公斤" in prompt
    assert "着装：" in prompt


def test_decode_base64_image_success_and_failure() -> None:
    img = Image.new("RGB", (10, 10), (1, 2, 3))
    buff = io.BytesIO()
    img.save(buff, format="PNG")
    b64 = base64.b64encode(buff.getvalue()).decode("utf-8")

    decoded = _decode_base64_image(b64)
    assert decoded is not None
    assert decoded.size == (10, 10)
    assert _decode_base64_image("not-valid-base64") is None


def test_extract_ark_image_from_data_url(monkeypatch) -> None:
    called: dict[str, str | None] = {"url": None}

    def fake_load(url: str):
        called["url"] = url
        return Image.new("RGB", (4, 4), (255, 255, 255))

    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._load_image_from_url", fake_load
    )
    out = _extract_ark_image({"data": [{"url": "http://example.com/a.png"}]})
    assert out is not None
    assert called["url"] == "http://example.com/a.png"


def test_extract_ark_image_from_output_content_base64(monkeypatch) -> None:
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._decode_base64_image",
        lambda *_: Image.new("RGB", (6, 6), (0, 0, 0)),
    )
    out = _extract_ark_image(
        {
            "output": [
                {
                    "content": [
                        {
                            "type": "image",
                            "image_base64": "abc",
                        }
                    ]
                }
            ]
        }
    )
    assert out is not None


def test_is_ark_configured_handles_exception(monkeypatch) -> None:
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator.get_ark_config",
        lambda: (_ for _ in ()).throw(RuntimeError("bad")),
    )
    assert _is_ark_configured() is False


def test_apply_id_photo_style_and_fallback_avatar() -> None:
    src = Image.new("RGB", (80, 80), (245, 245, 245))
    styled = AvatarGenerator._apply_id_photo_style(src, (80, 80), seed=123)
    assert styled.mode == "RGBA"
    assert styled.size == (80, 80)

    fallback = AvatarGenerator._generate_fallback_avatar((120, 160), "male")
    assert fallback.size == (120, 160)


def test_avatar_generator_generate_uses_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._generate_realistic_face",
        lambda **_: (_ for _ in ()).throw(RuntimeError("bad")),
    )
    out = AvatarGenerator.generate(size=(90, 120), backend="random_face")
    assert out.size == (90, 120)


def test_idcard_generate_and_batch_paths(tmp_path, monkeypatch) -> None:
    gen = IDCardImageGenerator()

    monkeypatch.setattr(
        gen, "_get_template", lambda: Image.new("RGB", (2200, 1400), (255, 255, 255))
    )
    monkeypatch.setattr(
        gen,
        "_get_font",
        lambda *_: ImageFont.load_default(),
    )

    identity = Identity.model_validate(
        {
            "name": "张三",
            "gender": "male",
            "ethnicity": "汉族",
            "address": "北京市朝阳区幸福路100号",
            "ssn": "110101199001011234",
            "birthdate": date(1990, 1, 1),
        }
    )

    out_file = tmp_path / "one.png"
    img = gen.generate(identity, output_path=out_file, include_avatar=False)
    assert img.size == (2200, 1400)
    assert out_file.exists()

    paths = gen.generate_batch([identity], tmp_path / "batch", include_avatar=False)
    assert len(paths) == 1
    assert paths[0].exists()


def test_generate_idcard_image_convenience(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator.IDCardImageGenerator.generate",
        lambda self, **kwargs: Image.new("RGB", (10, 10), (255, 255, 255)),
    )
    identity = Identity.model_validate({"name": "李四"})
    img = generate_idcard_image(
        identity, output_path=tmp_path / "x.png", include_avatar=False
    )
    assert img.size == (10, 10)


def test_get_template_missing_raises(tmp_path) -> None:
    gen = IDCardImageGenerator(assets_dir=tmp_path)
    with pytest.raises(FileNotFoundError):
        gen._get_template()


def test_interactive_model_setup_skip(monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda *_: "s")

    fake_config = SimpleNamespace(set_selected_model=lambda *_: True)
    fake_manager = SimpleNamespace(download_model=lambda *_: True)
    monkeypatch.setattr(
        "identity_gen.model_config.get_config_manager", lambda: fake_config
    )
    monkeypatch.setattr(
        "identity_gen.model_manager.get_model_manager", lambda: fake_manager
    )

    selected = _interactive_model_setup()
    assert selected is None


def test_generate_diffusers_face_without_selected_model(monkeypatch) -> None:
    fake_cfg = SimpleNamespace(get_selected_model=lambda: None)
    fake_mgr = SimpleNamespace()
    monkeypatch.setattr(
        "identity_gen.model_config.get_config_manager", lambda: fake_cfg
    )
    monkeypatch.setattr(
        "identity_gen.model_manager.get_model_manager", lambda: fake_mgr
    )
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._interactive_model_setup", lambda: None
    )

    assert _generate_diffusers_face(gender="male", seed=1, size=(50, 60)) is None


def test_generate_ark_face_success(monkeypatch) -> None:
    class FakeArk:
        def __init__(self, **_kwargs):
            self.images = SimpleNamespace(
                generate=lambda **_k: {"data": [{"image_base64": "abc"}]}
            )

    monkeypatch.setitem(
        sys.modules, "volcenginesdkarkruntime", SimpleNamespace(Ark=FakeArk)
    )
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator.get_ark_config",
        lambda: SimpleNamespace(
            api_key="k",
            base_url="https://x",
            model_id="m",
            timeout_seconds=30,
        ),
    )
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._extract_ark_image",
        lambda _resp: Image.new("RGB", (120, 80), (255, 255, 255)),
    )

    out = _generate_ark_face(gender="female", birthdate=date(2001, 1, 1), size=(40, 50))
    assert out is not None
    assert out.size == (40, 50)


def test_random_face_engine_and_realistic_face_paths(monkeypatch) -> None:
    class _Engine:
        def get_random_face(self):
            import numpy as np

            return np.zeros((64, 64, 3), dtype="uint8")

    ig._random_face_engine = None
    monkeypatch.setitem(
        sys.modules, "random_face", SimpleNamespace(get_engine=lambda: _Engine())
    )
    engine = ig._get_random_face_engine()
    assert engine is not None

    out = ig._generate_realistic_face(seed=1, size=(30, 40))
    assert out.size == (30, 40)


def test_random_face_engine_error(monkeypatch) -> None:
    ig._random_face_engine = None
    monkeypatch.setitem(
        sys.modules,
        "random_face",
        SimpleNamespace(get_engine=lambda: (_ for _ in ()).throw(RuntimeError("x"))),
    )
    with pytest.raises(RuntimeError):
        ig._get_random_face_engine()


def test_load_image_from_url_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("x")),
    )
    assert ig._load_image_from_url("https://example.com/a.png") is None


def test_extract_ark_image_object_branches(monkeypatch) -> None:
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._load_image_from_url",
        lambda *_: Image.new("RGB", (3, 3), (1, 1, 1)),
    )
    obj = SimpleNamespace(data=[SimpleNamespace(image_url="https://x")])
    assert ig._extract_ark_image(obj) is not None

    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._decode_base64_image",
        lambda *_: Image.new("RGB", (3, 3), (1, 1, 1)),
    )
    obj2 = SimpleNamespace(
        output=[SimpleNamespace(content=[SimpleNamespace(type="image", image="abc")])]
    )
    assert ig._extract_ark_image(obj2) is not None

    assert ig._extract_ark_image({"output": []}) is None
    assert ig._extract_ark_image(None) is None


def test_generate_ark_face_other_branches(monkeypatch) -> None:
    # no api key
    monkeypatch.setitem(
        sys.modules, "volcenginesdkarkruntime", SimpleNamespace(Ark=object)
    )
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator.get_ark_config",
        lambda: SimpleNamespace(
            api_key="", base_url="", model_id="", timeout_seconds=1
        ),
    )
    assert ig._generate_ark_face() is None

    # extract none
    class _Ark:
        def __init__(self, **_kwargs):
            self.images = SimpleNamespace(generate=lambda **_k: {"data": []})

    monkeypatch.setitem(
        sys.modules, "volcenginesdkarkruntime", SimpleNamespace(Ark=_Ark)
    )
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator.get_ark_config",
        lambda: SimpleNamespace(
            api_key="k", base_url="u", model_id="m", timeout_seconds=1
        ),
    )
    assert ig._generate_ark_face() is None


def test_generate_ark_face_importerror(monkeypatch):
    orig_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "volcenginesdkarkruntime":
            raise ImportError("missing")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)
    assert ig._generate_ark_face() is None


def test_interactive_model_setup_success_and_failure(monkeypatch) -> None:
    fake_config = SimpleNamespace(set_selected_model=lambda *_: True)
    fake_mgr_ok = SimpleNamespace(download_model=lambda *_: True)
    monkeypatch.setattr(
        "identity_gen.model_config.get_config_manager", lambda: fake_config
    )
    monkeypatch.setattr(
        "identity_gen.model_manager.get_model_manager", lambda: fake_mgr_ok
    )
    inputs = iter(["1"])
    monkeypatch.setattr("builtins.input", lambda *_: next(inputs))
    assert _interactive_model_setup() == "tiny-sd"

    fake_mgr_fail = SimpleNamespace(download_model=lambda *_: False)
    monkeypatch.setattr(
        "identity_gen.model_manager.get_model_manager", lambda: fake_mgr_fail
    )
    inputs2 = iter(["1"])
    monkeypatch.setattr("builtins.input", lambda *_: next(inputs2))
    assert _interactive_model_setup() is None


def test_interactive_model_setup_invalid_and_eof(monkeypatch) -> None:
    fake_config = SimpleNamespace(set_selected_model=lambda *_: True)
    fake_mgr = SimpleNamespace(download_model=lambda *_: True)
    monkeypatch.setattr(
        "identity_gen.model_config.get_config_manager", lambda: fake_config
    )
    monkeypatch.setattr(
        "identity_gen.model_manager.get_model_manager", lambda: fake_mgr
    )

    calls = iter(["x", "9", "1"])
    monkeypatch.setattr("builtins.input", lambda *_: next(calls))
    assert _interactive_model_setup() == "tiny-sd"

    monkeypatch.setattr("builtins.input", lambda *_: (_ for _ in ()).throw(EOFError()))
    assert _interactive_model_setup() in {"tiny-sd", "small-sd", "realistic-vision"}


def test_generate_diffusers_face_success_and_download_fail(monkeypatch) -> None:
    class _CfgMgr:
        def __init__(
            self,
            selected=(
                "tiny",
                SimpleNamespace(
                    name="Tiny",
                    format_prompt=lambda *_: "p",
                    negative_prompt="n",
                    guidance_scale=7.5,
                    num_inference_steps=20,
                ),
            ),
        ):
            self._selected = selected

        def get_selected_model(self):
            return self._selected

    class _Mgr:
        def __init__(self, available=True, download_ok=True):
            self.available = available
            self.download_ok = download_ok

        def is_model_available(self, _k):
            return self.available

        def download_model(self, _k):
            return self.download_ok

        def generate_image(self, **_kwargs):
            return Image.new("RGB", (100, 100), (255, 255, 255))

    monkeypatch.setattr(
        "identity_gen.model_config.get_config_manager", lambda: _CfgMgr()
    )
    monkeypatch.setattr(
        "identity_gen.model_manager.get_model_manager",
        lambda: _Mgr(available=False, download_ok=False),
    )
    assert _generate_diffusers_face() is None

    monkeypatch.setattr(
        "identity_gen.model_manager.get_model_manager",
        lambda: _Mgr(available=True, download_ok=True),
    )
    out = _generate_diffusers_face(gender="male", seed=3, size=(32, 48))
    assert out is not None
    assert out.size == (32, 48)


def test_avatar_generator_backend_selection_and_generate(monkeypatch) -> None:
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._is_ark_configured", lambda: True
    )
    monkeypatch.setitem(sys.modules, "volcenginesdkarkruntime", SimpleNamespace())
    assert AvatarGenerator._select_best_backend() == "ark"

    # force no diffusers and no random_face -> fallback
    AvatarGenerator._diffusers_checked = True
    AvatarGenerator._diffusers_available = False
    orig_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "random_face":
            raise ImportError("missing")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._is_ark_configured", lambda: False
    )
    assert AvatarGenerator._select_best_backend() == "fallback"

    # generate branches
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._generate_ark_face",
        lambda **_: Image.new("RGB", (20, 20), (255, 255, 255)),
    )
    out1 = AvatarGenerator.generate(size=(20, 20), backend="ark")
    assert out1.size == (20, 20)

    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._generate_diffusers_face",
        lambda **_: Image.new("RGB", (20, 20), (255, 255, 255)),
    )
    out2 = AvatarGenerator.generate(size=(20, 20), backend="diffusers")
    assert out2.size == (20, 20)


def test_idcard_font_template_and_generate_branches(tmp_path, monkeypatch) -> None:
    gen = IDCardImageGenerator(assets_dir=tmp_path)

    # font missing fallback
    f = gen._get_font("name")
    assert f is not None

    # template cache copy branch
    tpl = Image.new("RGB", (10, 10), (255, 255, 255))
    gen._template = tpl
    assert gen._get_template().size == (10, 10)

    # split address empty branch
    d = ImageDraw.Draw(Image.new("RGB", (10, 10), (255, 255, 255)))
    assert gen._split_address_lines(d, "\n\t ", gen._get_font("normal"), 100) == [""]

    # generate avatar exception path
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator.AvatarGenerator.generate",
        lambda **_: (_ for _ in ()).throw(RuntimeError("x")),
    )
    monkeypatch.setattr(
        gen, "_get_template", lambda: Image.new("RGB", (2200, 1400), (255, 255, 255))
    )
    monkeypatch.setattr(gen, "_get_font", lambda *_: ImageFont.load_default())
    identity = Identity.model_validate(
        {"name": "张三", "gender": "x", "address": "a", "ssn": "1"}
    )
    out = gen.generate(identity, include_avatar=True)
    assert out.size == (2200, 1400)


def test_generate_batch_exception_branch(tmp_path, monkeypatch) -> None:
    gen = IDCardImageGenerator()
    monkeypatch.setattr(
        gen, "generate", lambda **_: (_ for _ in ()).throw(RuntimeError("bad"))
    )
    identities = [Identity.model_validate({"name": "A", "ssn": "1"})]
    out = gen.generate_batch(identities, tmp_path)
    assert out == []


def test_more_idcard_helper_branches(monkeypatch) -> None:
    # _calculate_age branch where birthday not reached this year
    today = date.today()
    b = date(today.year - 20, min(today.month % 12 + 1, 12), min(today.day, 28))
    age = ig._calculate_age(b)
    assert age in {19, 20}

    # prompt clothing fallback line
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator.ID_PHOTO_DEFAULT_CLOTHING", ""
    )
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator.ID_PHOTO_CLOTHING_OPTIONS", ("校服",)
    )
    p = ig._build_id_photo_prompt("female", None, None)
    assert "着装：校服" in p

    # _is_ark_configured true branch
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator.get_ark_config",
        lambda: SimpleNamespace(api_key="x"),
    )
    assert ig._is_ark_configured() is True


def test_load_image_from_url_success(monkeypatch) -> None:
    img = Image.new("RGB", (5, 5), (255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return buf.getvalue()

    monkeypatch.setattr("urllib.request.urlopen", lambda *_a, **_k: _Resp())
    out = ig._load_image_from_url("https://example.com")
    assert out is not None


def test_generate_diffusers_face_exception_branch(monkeypatch) -> None:
    class _Cfg:
        def get_selected_model(self):
            return (
                "tiny",
                SimpleNamespace(
                    name="Tiny",
                    format_prompt=lambda *_: "p",
                    negative_prompt="n",
                    guidance_scale=7.5,
                    num_inference_steps=20,
                ),
            )

    class _Mgr:
        def is_model_available(self, _k):
            return True

        def generate_image(self, **_kwargs):
            raise RuntimeError("bad")

    monkeypatch.setattr("identity_gen.model_config.get_config_manager", lambda: _Cfg())
    monkeypatch.setattr("identity_gen.model_manager.get_model_manager", lambda: _Mgr())
    assert ig._generate_diffusers_face() is None


def test_avatar_generate_exception_fallbacks(monkeypatch) -> None:
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._generate_ark_face",
        lambda **_: (_ for _ in ()).throw(RuntimeError("x")),
    )
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._generate_realistic_face",
        lambda **_: Image.new("RGB", (30, 40), (1, 1, 1)),
    )
    out = AvatarGenerator.generate(size=(30, 40), backend="ark")
    assert out.size == (30, 40)

    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._generate_diffusers_face",
        lambda **_: (_ for _ in ()).throw(RuntimeError("x")),
    )
    out2 = AvatarGenerator.generate(size=(30, 40), backend="diffusers")
    assert out2.size == (30, 40)


def test_select_best_backend_diffusers_paths(monkeypatch):
    AvatarGenerator._diffusers_checked = False
    AvatarGenerator._diffusers_available = False
    if hasattr(AvatarGenerator, "_setup_attempted"):
        delattr(AvatarGenerator, "_setup_attempted")

    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._is_ark_configured", lambda: False
    )
    monkeypatch.setitem(sys.modules, "diffusers", SimpleNamespace())

    class _Cfg:
        def is_configured(self):
            return False

    monkeypatch.setattr("identity_gen.model_config.get_config_manager", lambda: _Cfg())
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._interactive_model_setup", lambda: None
    )
    monkeypatch.setitem(sys.modules, "random_face", SimpleNamespace())
    assert AvatarGenerator._select_best_backend() == "random_face"


def test_get_font_exception_branch(tmp_path, monkeypatch) -> None:
    gen = IDCardImageGenerator(assets_dir=tmp_path)
    font_path = tmp_path / "hei.ttf"
    font_path.write_bytes(b"not-a-font")
    default_font = ImageFont.load_default()
    monkeypatch.setattr(
        "PIL.ImageFont.truetype",
        lambda *_a, **_k: (_ for _ in ()).throw(OSError("bad")),
    )
    monkeypatch.setattr("PIL.ImageFont.load_default", lambda: default_font)
    f = gen._get_font("normal")
    assert f is not None


def test_split_address_line_wrapping_edges() -> None:
    gen = IDCardImageGenerator()
    img = Image.new("RGB", (100, 100), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font = gen._get_font("normal")
    lines = gen._split_address_lines(
        draw, "北京市海淀区中关村大街27号1101", font, 50, 2
    )
    assert len(lines) <= 2


def test_generate_with_rgba_avatar_and_no_birthdate(monkeypatch) -> None:
    gen = IDCardImageGenerator()
    monkeypatch.setattr(
        gen, "_get_template", lambda: Image.new("RGB", (2200, 1400), (255, 255, 255))
    )
    monkeypatch.setattr(gen, "_get_font", lambda *_: ImageFont.load_default())
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator.AvatarGenerator.generate",
        lambda **_: Image.new("RGBA", (500, 670), (255, 0, 0, 128)),
    )
    identity = Identity.model_validate(
        {
            "name": "王五",
            "gender": "male",
            "ethnicity": "汉族",
            "address": "北京",
            "ssn": "1",
        }
    )
    out = gen.generate(identity, include_avatar=True)
    assert out.size == (2200, 1400)


def test_cover_remaining_low_level_branches(monkeypatch) -> None:
    # realistic face RGB conversion branch + exception branch
    class _EngineRGBA:
        def get_random_face(self):
            import numpy as np

            return np.zeros((16, 16, 4), dtype="uint8")

    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._get_random_face_engine",
        lambda: _EngineRGBA(),
    )
    img = ig._generate_realistic_face(size=(8, 8))
    assert img.mode == "RGB"

    class _EngineBad:
        def get_random_face(self):
            raise RuntimeError("bad")

    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._get_random_face_engine",
        lambda: _EngineBad(),
    )
    with pytest.raises(RuntimeError):
        ig._generate_realistic_face(size=(8, 8))

    # extract data b64 branch and output fallback branches
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._decode_base64_image",
        lambda *_: Image.new("RGB", (2, 2), (0, 0, 0)),
    )
    assert ig._extract_ark_image({"data": [{"image_base64": "abc"}]}) is not None
    assert ig._extract_ark_image({"output": [{"content": [None]}]}) is None


def test_cover_ark_and_diffusers_remaining_branches(monkeypatch):
    # ark random.seed + convert RGBA + general exception
    seeds = {"v": None}
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator.random.seed",
        lambda s: seeds.__setitem__("v", s),
    )

    class _Ark:
        def __init__(self, **_kwargs):
            self.images = SimpleNamespace(
                generate=lambda **_k: {"data": [{"url": "u"}]}
            )

    monkeypatch.setitem(
        sys.modules, "volcenginesdkarkruntime", SimpleNamespace(Ark=_Ark)
    )
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator.get_ark_config",
        lambda: SimpleNamespace(
            api_key="k", base_url="u", model_id="m", timeout_seconds=1
        ),
    )
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._load_image_from_url",
        lambda _u: Image.new("RGBA", (12, 10), (255, 0, 0, 100)),
    )
    out = ig._generate_ark_face(seed=99, size=(6, 8))
    assert out is not None
    assert out.mode == "RGB"
    assert seeds["v"] == 99

    class _ArkBad:
        def __init__(self, **_kwargs):
            self.images = SimpleNamespace(
                generate=lambda **_k: (_ for _ in ()).throw(RuntimeError("boom"))
            )

    monkeypatch.setitem(
        sys.modules, "volcenginesdkarkruntime", SimpleNamespace(Ark=_ArkBad)
    )
    assert ig._generate_ark_face() is None

    # interactive setup EOF no recommended -> first model path
    monkeypatch.setattr(
        "identity_gen.model_config.DEFAULT_MODELS",
        {"x": {"name": "X", "size_gb": 1, "description": "d", "recommended": False}},
    )
    monkeypatch.setattr(
        "identity_gen.model_config.get_config_manager",
        lambda: SimpleNamespace(set_selected_model=lambda *_: True),
    )
    monkeypatch.setattr(
        "identity_gen.model_manager.get_model_manager",
        lambda: SimpleNamespace(download_model=lambda *_: True),
    )
    monkeypatch.setattr("builtins.input", lambda *_: (_ for _ in ()).throw(EOFError()))
    assert ig._interactive_model_setup() == "x"

    # interactive setup exception branch
    monkeypatch.setattr(
        "identity_gen.model_config.get_config_manager",
        lambda: (_ for _ in ()).throw(RuntimeError("x")),
    )
    assert ig._interactive_model_setup() is None

    # diffusers selected None -> setup returns key but still not selected => None (line 459/464)
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._interactive_model_setup", lambda: "tiny"
    )
    monkeypatch.setattr(
        "identity_gen.model_config.get_config_manager",
        lambda: SimpleNamespace(get_selected_model=lambda: None),
    )
    monkeypatch.setattr(
        "identity_gen.model_manager.get_model_manager", lambda: SimpleNamespace()
    )
    assert ig._generate_diffusers_face() is None


def test_cover_backend_selector_remaining_paths(monkeypatch):
    # ark configured but sdk import error -> continue
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._is_ark_configured", lambda: True
    )
    AvatarGenerator._diffusers_checked = False
    AvatarGenerator._diffusers_available = False
    orig_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "volcenginesdkarkruntime":
            raise ImportError("missing")
        if name == "diffusers":
            raise ImportError("missing")
        if name == "random_face":
            return SimpleNamespace()
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)
    assert AvatarGenerator._select_best_backend() == "random_face"

    # diffusers available + configured
    AvatarGenerator._diffusers_checked = True
    AvatarGenerator._diffusers_available = True
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._is_ark_configured", lambda: False
    )
    monkeypatch.setattr(
        "identity_gen.model_config.get_config_manager",
        lambda: SimpleNamespace(is_configured=lambda: True),
    )
    assert AvatarGenerator._select_best_backend() == "diffusers"

    # diffusers available + setup returns key
    if hasattr(AvatarGenerator, "_setup_attempted"):
        delattr(AvatarGenerator, "_setup_attempted")
    monkeypatch.setattr(
        "identity_gen.model_config.get_config_manager",
        lambda: SimpleNamespace(is_configured=lambda: False),
    )
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._interactive_model_setup", lambda: "tiny"
    )
    assert AvatarGenerator._select_best_backend() == "diffusers"

    # final fallback branch when random_face missing
    if hasattr(AvatarGenerator, "_setup_attempted"):
        delattr(AvatarGenerator, "_setup_attempted")
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._interactive_model_setup", lambda: None
    )

    def fake_import2(name, *args, **kwargs):
        if name == "random_face":
            raise ImportError("missing")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import2)
    assert AvatarGenerator._select_best_backend() == "fallback"


def test_avatar_generate_auto_branch(monkeypatch):
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator.AvatarGenerator._select_best_backend",
        lambda: "fallback",
    )
    out = AvatarGenerator.generate(size=(12, 16), backend="auto")
    assert out.size == (12, 16)


def test_cover_remaining_specific_lines(monkeypatch, tmp_path):
    # extract: content empty (258), type=image url (280), fallback url/base64 (285/287)
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._load_image_from_url",
        lambda *_: Image.new("RGB", (1, 1), (1, 1, 1)),
    )
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._decode_base64_image",
        lambda *_: Image.new("RGB", (1, 1), (1, 1, 1)),
    )
    assert ig._extract_ark_image({"output": [{"content": None}]}) is None
    assert (
        ig._extract_ark_image(
            {"output": [{"content": [{"type": "image/png", "image_url": "u"}]}]}
        )
        is not None
    )
    assert (
        ig._extract_ark_image(
            {"output": [{"content": [{"type": "text", "image_url": "u"}]}]}
        )
        is not None
    )
    assert (
        ig._extract_ark_image(
            {"output": [{"content": [{"type": "text", "image": "abc"}]}]}
        )
        is not None
    )

    # diffusers: image none (507), importerror (510-511)
    monkeypatch.setattr(
        "identity_gen.model_config.get_config_manager",
        lambda: SimpleNamespace(
            get_selected_model=lambda: (
                "tiny",
                SimpleNamespace(
                    name="t",
                    format_prompt=lambda *_: "p",
                    negative_prompt="n",
                    guidance_scale=1,
                    num_inference_steps=1,
                ),
            )
        ),
    )
    monkeypatch.setattr(
        "identity_gen.model_manager.get_model_manager",
        lambda: SimpleNamespace(
            is_model_available=lambda _k: True, generate_image=lambda **_k: None
        ),
    )
    assert ig._generate_diffusers_face() is None

    orig_import = __import__

    def fake_import(name, *args, **kwargs):
        if name.endswith("model_manager"):
            raise ImportError("x")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)
    assert ig._generate_diffusers_face() is None
    monkeypatch.setattr("builtins.__import__", orig_import)

    # _select_best_backend import model_config fail (651-652)
    AvatarGenerator._diffusers_checked = True
    AvatarGenerator._diffusers_available = True
    if hasattr(AvatarGenerator, "_setup_attempted"):
        delattr(AvatarGenerator, "_setup_attempted")
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator._is_ark_configured", lambda: False
    )

    def fake_import_cfg(name, *args, **kwargs):
        if name.endswith("model_config"):
            raise ImportError("x")
        if name == "random_face":
            return SimpleNamespace()
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import_cfg)
    assert AvatarGenerator._select_best_backend() == "random_face"
    monkeypatch.setattr("builtins.__import__", orig_import)

    # apply style non-RGB path (670)
    rgba = Image.new("RGBA", (20, 20), (250, 250, 250, 255))
    styled = AvatarGenerator._apply_id_photo_style(rgba, (20, 20), seed=2)
    assert styled.mode == "RGBA"

    # normalize RGB path (755)
    rgb = Image.new("RGB", (20, 20), (0, 0, 0))
    norm = AvatarGenerator._normalize_avatar_composition(rgb, (20, 20))
    assert norm.size == (20, 20)

    # _get_font cache path (862)
    g = IDCardImageGenerator()
    _ = g._get_font("normal")
    _ = g._get_font("normal")

    # _get_template load path (904-905)
    assets = tmp_path / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (10, 10), (255, 255, 255)).save(assets / "empty.png")
    gt = IDCardImageGenerator(assets_dir=assets)
    assert gt._get_template().size == (10, 10)

    # split address current=ch path (939)
    draw = ImageDraw.Draw(Image.new("RGB", (30, 30), (255, 255, 255)))
    lines = gt._split_address_lines(
        draw, "中华人民共和国", gt._get_font("normal"), 5, 3
    )
    assert len(lines) >= 1

    # generate avatar non-RGBA paste branch (974)
    monkeypatch.setattr(
        gt, "_get_template", lambda: Image.new("RGB", (2200, 1400), (255, 255, 255))
    )
    monkeypatch.setattr(gt, "_get_font", lambda *_: ImageFont.load_default())
    monkeypatch.setattr(
        "identity_gen.idcard_image_generator.AvatarGenerator.generate",
        lambda **_: Image.new("RGB", (500, 670), (255, 0, 0)),
    )
    identity = Identity.model_validate(
        {
            "name": "赵六",
            "gender": "male",
            "ethnicity": "汉族",
            "address": "北京",
            "ssn": "1",
        }
    )
    out = gt.generate(identity, include_avatar=True)
    assert out.size == (2200, 1400)
