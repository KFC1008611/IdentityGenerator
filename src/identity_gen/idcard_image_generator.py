"""Chinese ID card image generator with realistic avatar generation.

Supports multiple backends:
- ark: Volcano Ark SDK for AI-generated ID photos
- diffusers: High-quality generation using Stable Diffusion models (user-selectable)
- random_face: Lightweight fallback using random_face library
- fallback: Basic silhouette generation (no external dependencies)
"""

import base64
import hashlib
import io
import logging
import random
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any, Optional, Tuple, Union

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from .config import (
    ID_PHOTO_AGE_GENDER_LABELS,
    ID_PHOTO_BASE_PROMPT,
    ID_PHOTO_BAREHEAD,
    ID_PHOTO_CLOTHING_OPTIONS,
    ID_PHOTO_DEFAULT_CLOTHING,
    get_ark_config,
)
from .models import Identity

logger = logging.getLogger(__name__)

# Global engine instance for random_face
_random_face_engine = None


def _get_random_face_engine():
    """Get or create the random_face engine singleton."""
    global _random_face_engine
    if _random_face_engine is None:
        try:
            import random_face

            _random_face_engine = random_face.get_engine()
            logger.debug("random_face engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize random_face engine: {e}")
            raise
    return _random_face_engine


def _generate_realistic_face(
    seed: Optional[int] = None, size: Tuple[int, int] = (500, 670)
) -> Image.Image:
    """Generate a realistic human face using random_face library.

    Args:
        seed: Random seed for reproducible face generation
        size: Target size (width, height)

    Returns:
        PIL Image of the face
    """
    try:
        # Set numpy random seed for reproducibility
        if seed is not None:
            np.random.seed(seed)

        # Get engine and generate face
        engine = _get_random_face_engine()
        face_array = engine.get_random_face()

        # Convert numpy array to PIL Image
        # face_array is uint8, shape (1024, 1024, 3)
        # random_face returns BGR format, need to convert to RGB
        if face_array.shape[-1] == 3:
            # Convert BGR to RGB
            face_array = face_array[:, :, ::-1]

        face_img = Image.fromarray(face_array)

        # Ensure RGB mode
        if face_img.mode != "RGB":
            face_img = face_img.convert("RGB")

        face_img = _smart_resize(face_img, size)

        return face_img

    except Exception as e:
        logger.error(f"Failed to generate realistic face: {e}")
        raise


def _smart_resize(img: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
    target_w, target_h = target_size
    img_w, img_h = img.size
    scale_w = target_w / img_w
    scale_h = target_h / img_h
    scale = max(scale_w, scale_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)
    img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    right = left + target_w
    bottom = top + target_h

    img_cropped = img_resized.crop((left, top, right, bottom))

    return img_cropped


def _calculate_age(birthdate: Optional[date]) -> Optional[int]:
    if birthdate is None:
        return None

    today = date.today()
    age = today.year - birthdate.year
    if (today.month, today.day) < (birthdate.month, birthdate.day):
        age -= 1
    return max(age, 0)


def _age_bucket(age: Optional[int]) -> str:
    if age is None:
        return "adult"
    if age <= 12:
        return "child"
    if age <= 17:
        return "teen"
    if age <= 29:
        return "young_adult"
    if age <= 59:
        return "adult"
    return "senior"


def _gender_key(gender: Optional[str]) -> str:
    if gender is None:
        return "unknown"
    gender_lower = gender.lower()
    if gender_lower in ("male", "man", "boy"):
        return "male"
    if gender_lower in ("female", "woman", "girl"):
        return "female"
    return "unknown"


def _build_id_photo_prompt(
    gender: Optional[str],
    birthdate: Optional[date],
    identity: Optional[Identity] = None,
) -> str:
    age = _calculate_age(birthdate)
    bucket = _age_bucket(age)
    gender_label_group = ID_PHOTO_AGE_GENDER_LABELS.get(_gender_key(gender), {})
    gender_label = gender_label_group.get(bucket, "成年人")

    clothing = ID_PHOTO_DEFAULT_CLOTHING
    if not clothing and ID_PHOTO_CLOTHING_OPTIONS:
        clothing = ID_PHOTO_CLOTHING_OPTIONS[0]

    prompt = f"{gender_label}，{ID_PHOTO_BASE_PROMPT}"
    if age is not None:
        prompt += f" 年龄约{age}岁。"
    if identity and identity.height:
        prompt += f" 身高约{identity.height}厘米。"
    if identity and identity.weight:
        prompt += f" 体重约{identity.weight}公斤。"
    if clothing:
        prompt += f" 着装：{clothing}。"
    if ID_PHOTO_BAREHEAD:
        prompt += " 发型整洁，头发不遮挡眉眼耳朵。"
    return prompt


def _load_image_from_url(image_url: str) -> Optional[Image.Image]:
    try:
        with urllib.request.urlopen(image_url, timeout=30) as response:
            data = response.read()
        return Image.open(io.BytesIO(data))
    except Exception as e:
        logger.error(f"Failed to load image from URL: {e}")
        return None


def _decode_base64_image(data: str) -> Optional[Image.Image]:
    try:
        image_bytes = base64.b64decode(data)
        return Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        logger.error(f"Failed to decode base64 image: {e}")
        return None


def _extract_ark_image(response: Any) -> Optional[Image.Image]:
    if response is None:
        return None

    data_items = None
    if isinstance(response, dict):
        data_items = response.get("data")
    else:
        data_items = getattr(response, "data", None)

    if data_items:
        for item in data_items:
            if isinstance(item, dict):
                image_url = item.get("url") or item.get("image_url")
                image_base64 = (
                    item.get("b64_json")
                    or item.get("image_base64")
                    or item.get("image")
                )
            else:
                image_url = getattr(item, "url", None) or getattr(
                    item, "image_url", None
                )
                image_base64 = (
                    getattr(item, "b64_json", None)
                    or getattr(item, "image_base64", None)
                    or getattr(item, "image", None)
                )

            if image_url:
                return _load_image_from_url(image_url)
            if image_base64:
                return _decode_base64_image(image_base64)

    outputs = None
    if isinstance(response, dict):
        outputs = response.get("output") or response.get("data")
    else:
        outputs = getattr(response, "output", None) or getattr(response, "data", None)

    if not outputs:
        return None

    for output_item in outputs:
        if isinstance(output_item, dict):
            content = output_item.get("content")
        else:
            content = getattr(output_item, "content", None)

        if not content:
            continue

        for content_item in content:
            if isinstance(content_item, dict):
                item_type = content_item.get("type")
                image_url = content_item.get("image_url")
                image_base64 = (
                    content_item.get("image_base64")
                    or content_item.get("b64_json")
                    or content_item.get("image")
                )
            else:
                item_type = getattr(content_item, "type", None)
                image_url = getattr(content_item, "image_url", None)
                image_base64 = (
                    getattr(content_item, "image_base64", None)
                    or getattr(content_item, "b64_json", None)
                    or getattr(content_item, "image", None)
                )

            if item_type and "image" in str(item_type):
                if image_url:
                    return _load_image_from_url(image_url)
                if image_base64:
                    return _decode_base64_image(image_base64)

            if image_url:
                return _load_image_from_url(image_url)
            if image_base64:
                return _decode_base64_image(image_base64)

    return None


def _is_ark_configured() -> bool:
    try:
        config = get_ark_config()
        return bool(config.api_key)
    except Exception:
        return False


def _generate_ark_face(
    gender: Optional[str] = None,
    birthdate: Optional[date] = None,
    identity: Optional[Identity] = None,
    seed: Optional[int] = None,
    size: Tuple[int, int] = (500, 670),
) -> Optional[Image.Image]:
    try:
        from volcenginesdkarkruntime import Ark

        config = get_ark_config()
        if not config.api_key:
            logger.warning("ARK API key is not configured")
            return None

        if seed is not None:
            random.seed(seed)

        prompt = _build_id_photo_prompt(gender, birthdate, identity)
        client = Ark(
            base_url=config.base_url,
            api_key=config.api_key,
        )

        response = client.images.generate(
            model=config.model_id,
            prompt=prompt,
            response_format="b64_json",
            seed=seed,
            timeout=config.timeout_seconds,
        )

        image = _extract_ark_image(response)
        if image is None:
            return None

        if image.mode != "RGB":
            image = image.convert("RGB")

        image = _smart_resize(image, size)
        return image
    except ImportError as e:
        logger.debug(f"Ark SDK not available: {e}")
        return None
    except Exception as e:
        logger.error(f"Ark generation failed: {e}")
        return None


def _interactive_model_setup() -> Optional[str]:
    """Interactive model selection and download.

    Returns:
        Selected model key or None if cancelled/failed
    """
    try:
        from .model_config import get_config_manager, DEFAULT_MODELS
        from .model_manager import get_model_manager

        config_manager = get_config_manager()
        model_manager = get_model_manager()

        print("\n" + "=" * 60)
        print("🎨 AI 头像模型配置")
        print("=" * 60)
        print("\n首次使用需要下载 AI 模型来生成高质量头像。")
        print("模型只需下载一次，后续会自动使用。\n")

        # Show available models
        print("可用模型:")
        models_list = list(DEFAULT_MODELS.items())
        for i, (key, data) in enumerate(models_list, 1):
            recommended = " ★推荐" if data.get("recommended") else ""
            print(f"  {i}. {data['name']} (~{data['size_gb']} GB){recommended}")
            print(f"     {data['description']}")
        print()

        # Get user choice
        while True:
            try:
                choice = input("请选择模型 (1-3) 或输入 's' 跳过: ").strip()
                if choice.lower() == "s":
                    print("已跳过模型配置，将使用备用方案生成头像。")
                    return None

                idx = int(choice) - 1
                if 0 <= idx < len(models_list):
                    selected_key, selected_model = models_list[idx]
                    break
                else:
                    print("❌ 无效选择，请输入 1-3")
            except ValueError:
                print("❌ 无效输入，请输入数字或 's'")
            except EOFError:
                # Non-interactive mode (piped input)
                print("\n检测到非交互模式，自动选择推荐模型...")
                for key, data in models_list:
                    if data.get("recommended"):
                        selected_key, selected_model = key, data
                        break
                else:
                    selected_key, selected_model = models_list[0]
                break

        print(f"\n✓ 已选择: {selected_model['name']}")

        # Download model
        print(
            f"\n正在下载 {selected_model['name']} (~{selected_model['size_gb']} GB)..."
        )
        print("下载时间取决于网络速度，请耐心等待...\n")

        success = model_manager.download_model(selected_key)

        if success:
            config_manager.set_selected_model(selected_key)
            print(f"\n✅ {selected_model['name']} 下载完成！")
            print("现在可以生成高质量 AI 头像了。\n")
            return selected_key
        else:
            print(f"\n❌ 下载失败，将使用备用方案。")
            return None

    except Exception as e:
        logger.error(f"Model setup failed: {e}")
        return None


def _generate_diffusers_face(
    gender: Optional[str] = None,
    seed: Optional[int] = None,
    size: Tuple[int, int] = (500, 670),
) -> Optional[Image.Image]:
    """Generate a realistic human face using diffusers library with transparent background.

    Args:
        gender: Gender for generation ('male' or 'female')
        seed: Random seed for reproducibility
        size: Target size (width, height)

    Returns:
        PIL Image of the face with transparent background, or None if generation failed
    """
    try:
        from .model_manager import get_model_manager
        from .model_config import get_config_manager

        manager = get_model_manager()
        config_manager = get_config_manager()

        # Check if model is configured and downloaded
        selected = config_manager.get_selected_model()
        model_key = None

        if selected is None:
            # No model configured, try interactive setup
            model_key = _interactive_model_setup()
            if model_key is None:
                return None
            selected = config_manager.get_selected_model()
        else:
            model_key = selected[0]

        if selected is None:
            return None

        model_key, model_config = selected

        # Check if model is downloaded
        if not manager.is_model_available(model_key):
            print(f"\n模型 {model_key} 需要下载...")
            if not manager.download_model(model_key):
                print(f"❌ 模型下载失败")
                return None

        print(f"🎨 正在使用 {model_config.name} 生成头像...")

        # Generate image
        prompt = model_config.format_prompt(gender or "person")
        negative_prompt = model_config.negative_prompt

        logger.debug(f"Generating with prompt: {prompt}")

        # Calculate generation size to match target aspect ratio
        # Target ratio: width/height = 500/670 ≈ 0.746
        target_ratio = size[0] / size[1]
        gen_width = 512
        gen_height = int(gen_width / target_ratio)
        # Ensure height is multiple of 8 for SD models
        gen_height = (gen_height // 8) * 8

        image = manager.generate_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            guidance_scale=model_config.guidance_scale,
            num_inference_steps=model_config.num_inference_steps,
            seed=seed,
            height=gen_height,
            width=gen_width,
            model_key=model_key,
        )

        if image is not None:
            print("✓ 头像生成成功")
            image = _smart_resize(image, size)
            return image

        return None

    except ImportError as e:
        logger.debug(f"Diffusers not available: {e}")
        return None

    except Exception as e:
        logger.error(f"Diffusers generation failed: {e}")
        return None


class AvatarGenerator:
    """Generate realistic avatar images for ID cards.

    Supports multiple backends in order of preference:
    1. ark: Volcano Ark SDK (LLM image generation)
    2. diffusers: High-quality Stable Diffusion models (user-configurable)
    3. random_face: Lightweight MobileStyleGAN (12MB, no GPU needed)
    4. fallback: Basic silhouette (no dependencies)
    """

    # Generation backend preference
    DEFAULT_BACKEND = "auto"  # "auto", "ark", "diffusers", "random_face", "fallback"

    @classmethod
    def generate(
        cls,
        size: Tuple[int, int] = (500, 670),
        gender: Optional[str] = None,
        birthdate: Optional[date] = None,
        identity: Optional[Identity] = None,
        seed: Optional[int] = None,
        backend: str = "auto",
    ) -> Image.Image:
        """Generate a realistic avatar image.

        Args:
            size: Target size (width, height)
            gender: Gender ('male' or 'female')
            birthdate: Birthdate for age-specific prompt
            identity: Full identity for variation cues
            seed: Random seed for reproducibility
            backend: Generation backend to use ("auto", "ark", "diffusers", "random_face", "fallback")

        Returns:
            PIL Image of the avatar
        """
        if backend == "auto":
            backend = cls._select_best_backend()

        # Try specified backend first
        if backend == "ark":
            try:
                image = _generate_ark_face(
                    gender=gender,
                    birthdate=birthdate,
                    identity=identity,
                    seed=seed,
                    size=size,
                )
                if image is not None:
                    return cls._apply_id_photo_style(image, size, seed=seed)
            except Exception as e:
                logger.warning(f"Ark generation failed: {e}")

        if backend == "diffusers":
            try:
                image = _generate_diffusers_face(gender=gender, seed=seed, size=size)
                if image is not None:
                    return cls._apply_id_photo_style(image, size, seed=seed)
            except Exception as e:
                logger.warning(f"Diffusers generation failed: {e}")

        # Fallback to random_face
        if backend in ("ark", "diffusers", "random_face"):
            try:
                face = _generate_realistic_face(seed=seed, size=size)
                return cls._apply_id_photo_style(face, size, seed=seed)
            except Exception as e:
                logger.warning(f"random_face generation failed: {e}")

        # Final fallback to basic silhouette
        return cls._generate_fallback_avatar(size, gender)

    _diffusers_checked: bool = False
    _diffusers_available: bool = False

    @classmethod
    def _select_best_backend(cls) -> str:
        """Select the best available backend."""
        # Prefer Ark if configured
        if _is_ark_configured():
            try:
                import volcenginesdkarkruntime

                return "ark"
            except ImportError:
                logger.debug("Ark SDK not installed, skipping Ark backend")

        # First check if diffusers is available
        if not cls._diffusers_checked:
            cls._diffusers_checked = True
            try:
                import diffusers

                cls._diffusers_available = True
            except ImportError:
                cls._diffusers_available = False
                logger.debug("diffusers not installed, skipping AI model selection")

        # If diffusers is not available, use random_face directly
        if not cls._diffusers_available:
            try:
                import random_face

                return "random_face"
            except ImportError:
                return "fallback"

        # diffusers is available, check if configured
        try:
            from .model_config import get_config_manager

            config_manager = get_config_manager()

            # Check if diffusers is configured and model is downloaded
            if config_manager.is_configured():
                return "diffusers"

            # Not configured - try interactive setup (only once)
            if not hasattr(cls, "_setup_attempted"):
                cls._setup_attempted = True
                print("\n🎨 AI 头像生成首次使用配置")
                print("-" * 50)
                print("检测到没有配置 AI 模型。")
                print("你可以选择下载 AI 模型来生成高质量头像，")
                print("或按 's' 跳过使用备用方案。\n")

                model_key = _interactive_model_setup()
                if model_key is not None:
                    return "diffusers"
        except ImportError:
            pass

        # Fallback to random_face
        try:
            import random_face

            return "random_face"
        except ImportError:
            pass

        return "fallback"

    @classmethod
    def _apply_id_photo_style(
        cls, img: Image.Image, target_size: Tuple[int, int], seed: Optional[int] = None
    ) -> Image.Image:
        """Apply ID photo styling to the face image and make background transparent."""
        if img.mode != "RGB":
            img_rgb = img.convert("RGB")
        else:
            img_rgb = img

        img_rgb = img_rgb.filter(ImageFilter.GaussianBlur(radius=0.3))
        img_rgb = cls._add_subtle_noise(img_rgb, seed=seed)

        enhancer = ImageEnhance.Brightness(img_rgb)
        img_rgb = enhancer.enhance(1.02)
        enhancer = ImageEnhance.Contrast(img_rgb)
        img_rgb = enhancer.enhance(1.05)
        enhancer = ImageEnhance.Sharpness(img_rgb)
        img_rgb = enhancer.enhance(1.1)

        img_rgba = img_rgb.convert("RGBA")
        rgba = np.array(img_rgba)
        rgb = rgba[:, :, :3].astype(np.int16)
        height, width = rgb.shape[:2]
        if height == 0 or width == 0:
            return img_rgba

        border = np.concatenate(
            [rgb[0, :, :], rgb[height - 1, :, :], rgb[:, 0, :], rgb[:, width - 1, :]],
            axis=0,
        )
        bg = np.median(border, axis=0)
        diff = np.sqrt(np.sum((rgb - bg) ** 2, axis=2))
        brightness = rgb.mean(axis=2)
        mask = (diff <= 35) & (brightness >= 200)

        visited = np.zeros((height, width), dtype=bool)
        stack = []

        for x in range(width):
            if mask[0, x]:
                visited[0, x] = True
                stack.append((0, x))
            if mask[height - 1, x] and not visited[height - 1, x]:
                visited[height - 1, x] = True
                stack.append((height - 1, x))

        for y in range(1, height - 1):
            if mask[y, 0]:
                visited[y, 0] = True
                stack.append((y, 0))
            if mask[y, width - 1] and not visited[y, width - 1]:
                visited[y, width - 1] = True
                stack.append((y, width - 1))

        while stack:
            y, x = stack.pop()
            ny = y - 1
            if ny >= 0 and mask[ny, x] and not visited[ny, x]:
                visited[ny, x] = True
                stack.append((ny, x))
            ny = y + 1
            if ny < height and mask[ny, x] and not visited[ny, x]:
                visited[ny, x] = True
                stack.append((ny, x))
            nx = x - 1
            if nx >= 0 and mask[y, nx] and not visited[y, nx]:
                visited[y, nx] = True
                stack.append((y, nx))
            nx = x + 1
            if nx < width and mask[y, nx] and not visited[y, nx]:
                visited[y, nx] = True
                stack.append((y, nx))

        alpha = np.where(visited, 0, 255).astype(np.uint8)
        alpha_img = Image.fromarray(alpha, mode="L").filter(
            ImageFilter.GaussianBlur(radius=1)
        )
        rgba[:, :, 3] = np.array(alpha_img)

        return Image.fromarray(rgba, mode="RGBA")

    @classmethod
    def _add_subtle_noise(
        cls, img: Image.Image, seed: Optional[int] = None
    ) -> Image.Image:
        """Add subtle noise for photo realism."""
        if seed is not None:
            np.random.seed(
                seed + 999
            )  # Use different seed offset to avoid affecting face generation
        img_array = np.array(img).astype(np.float32)
        noise = np.random.normal(0, 1.5, img_array.shape)
        img_array = np.clip(img_array + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(img_array)

    @classmethod
    def _generate_fallback_avatar(
        cls, size: Tuple[int, int], gender: Optional[str] = None
    ) -> Image.Image:
        """Generate a simple fallback avatar if realistic generation fails."""
        # Create a simple gray background
        img = Image.new("RGB", size, (240, 240, 240))
        draw = ImageDraw.Draw(img)

        # Draw simple avatar silhouette
        center_x = size[0] // 2
        center_y = size[1] // 2

        # Head circle
        head_radius = min(size) // 4
        draw.ellipse(
            [
                center_x - head_radius,
                center_y - head_radius - 20,
                center_x + head_radius,
                center_y + head_radius - 20,
            ],
            fill=(200, 180, 160),
            outline=(180, 160, 140),
            width=2,
        )

        # Body silhouette
        body_width = head_radius * 2
        draw.polygon(
            [
                (center_x - body_width, size[1]),
                (center_x - body_width // 2, center_y + head_radius // 2),
                (center_x + body_width // 2, center_y + head_radius // 2),
                (center_x + body_width, size[1]),
            ],
            fill=(100, 100, 120),
        )

        return img


class IDCardImageGenerator:
    """Generator for Chinese ID card images using original template."""

    def __init__(self, assets_dir: Optional[Path] = None):
        """Initialize the ID card image generator.

        Args:
            assets_dir: Directory containing font files and template.
        """
        if assets_dir is None:
            self.assets_dir = Path(__file__).parent / "data" / "assets"
        else:
            self.assets_dir = Path(assets_dir)
        self.assets_dir = Path(self.assets_dir)
        self._fonts: dict[str, Any] = {}
        self._template: Optional[Image.Image] = None

    def _get_font(self, font_type: str = "normal") -> ImageFont.FreeTypeFont:
        """Get or load a font."""
        if font_type in self._fonts:
            return self._fonts[font_type]

        font_paths = {
            "name": self.assets_dir / "hei.ttf",
            "normal": self.assets_dir / "hei.ttf",
            "date": self.assets_dir / "fzhei.ttf",
            "id": self.assets_dir / "ocrb10bt.ttf",
        }

        font_sizes = {
            "name": 72,
            "normal": 60,
            "date": 60,
            "id": 72,
        }

        font_path = font_paths.get(font_type, self.assets_dir / "hei.ttf")
        font_size = font_sizes.get(font_type, 60)

        if not font_path.exists():
            logger.warning(f"Font not found: {font_path}, using default")
            self._fonts[font_type] = ImageFont.load_default()
            return self._fonts[font_type]

        try:
            font = ImageFont.truetype(str(font_path), font_size)
            self._fonts[font_type] = font
            return self._fonts[font_type]
        except Exception as e:
            logger.warning(f"Failed to load font {font_path}: {e}")
            self._fonts[font_type] = ImageFont.load_default()
            return self._fonts[font_type]

    def _get_template(self) -> Image.Image:
        """Load the ID card template image."""
        if self._template is not None:
            return self._template.copy()

        template_path = self.assets_dir / "empty.png"
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        self._template = Image.open(template_path)
        return self._template.copy()

    def generate(
        self,
        identity: Identity,
        output_path: Optional[Union[str, Path]] = None,
        include_avatar: bool = True,
        avatar_seed: Optional[int] = None,
        avatar_backend: str = "auto",
    ) -> Image.Image:
        """Generate an ID card image from an Identity object.

        Uses the original template and layout from the reference implementation.
        """
        im = self._get_template()

        if include_avatar:
            try:
                avatar = AvatarGenerator.generate(
                    size=(500, 670),
                    gender=identity.gender,
                    birthdate=identity.birthdate,
                    identity=identity,
                    seed=avatar_seed,
                    backend=avatar_backend,
                )
                # Ensure avatar mode is correct
                if avatar.mode == "RGBA":
                    im.paste(avatar, (1500, 690), mask=avatar)
                else:
                    im.paste(avatar, (1500, 690))
            except Exception as e:
                logger.error(f"Failed to generate avatar: {e}")

        name_font = self._get_font("name")
        other_font = self._get_font("normal")
        bdate_font = self._get_font("date")
        id_font = self._get_font("id")

        draw = ImageDraw.Draw(im)

        name = identity.name or ""
        gender = identity.gender or ""
        ethnicity = identity.ethnicity or ""
        address = identity.address or ""
        id_number = identity.ssn or ""

        if identity.birthdate:
            year = str(identity.birthdate.year)
            month = str(identity.birthdate.month)
            day = str(identity.birthdate.day)
        else:
            year = ""
            month = ""
            day = ""

        gender_cn = "男" if gender == "male" else "女" if gender == "female" else gender

        draw.text((630, 690), name, fill=(0, 0, 0), font=name_font)
        draw.text((630, 840), gender_cn, fill=(0, 0, 0), font=other_font)
        draw.text((1030, 840), ethnicity, fill=(0, 0, 0), font=other_font)
        draw.text((630, 980), year, fill=(0, 0, 0), font=bdate_font)
        draw.text((950, 980), month, fill=(0, 0, 0), font=bdate_font)
        draw.text((1150, 980), day, fill=(0, 0, 0), font=bdate_font)

        start = 0
        loc = 1120
        while start + 11 < len(address):
            draw.text(
                (630, loc), address[start : start + 11], fill=(0, 0, 0), font=other_font
            )
            start += 11
            loc += 100
        draw.text((630, loc), address[start:], fill=(0, 0, 0), font=other_font)

        draw.text((950, 1475), id_number, fill=(0, 0, 0), font=id_font)

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            im.save(output_path, "PNG")
            logger.info(f"ID card image saved to: {output_path}")

        return im

    def generate_batch(
        self,
        identities: list[Identity],
        output_dir: Union[str, Path],
        filename_pattern: str = "{name}_idcard.png",
        include_avatar: bool = True,
        avatar_backend: str = "auto",
    ) -> list[Path]:
        """Generate ID card images for multiple identities."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_paths: list[Path] = []

        for i, identity in enumerate(identities):
            filename = filename_pattern.format(
                name=identity.name or f"identity_{i}",
                ssn=identity.ssn or f"id_{i}",
                index=i,
            )

            output_path = output_dir / filename

            try:
                self.generate(
                    identity=identity,
                    output_path=output_path,
                    include_avatar=include_avatar,
                    avatar_seed=i,
                    avatar_backend=avatar_backend,
                )
                saved_paths.append(output_path)
            except Exception as e:
                logger.error(f"Failed to generate ID card for {identity.name}: {e}")

        return saved_paths


def generate_idcard_image(
    identity: Identity,
    output_path: Optional[Union[str, Path]] = None,
    include_avatar: bool = True,
    seed: Optional[int] = None,
    avatar_backend: str = "auto",
) -> Image.Image:
    """Convenience function to generate a single ID card image."""
    generator = IDCardImageGenerator()
    return generator.generate(
        identity=identity,
        output_path=output_path,
        include_avatar=include_avatar,
        avatar_seed=seed,
        avatar_backend=avatar_backend,
    )
