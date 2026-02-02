"""Chinese ID card image generator with avatar generation."""

import logging
import random
from pathlib import Path
from typing import Optional, Tuple, Union

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .models import Identity

logger = logging.getLogger(__name__)


class AvatarGenerator:
    """Generate random avatar images for ID cards using Pillow."""

    SKIN_TONES = [
        (255, 224, 189),
        (240, 200, 160),
        (220, 175, 140),
        (190, 145, 110),
        (160, 115, 85),
    ]

    HAIR_COLORS = [
        (0, 0, 0),
        (44, 34, 43),
        (80, 68, 68),
        (100, 85, 75),
        (180, 165, 140),
        (128, 128, 128),
        (220, 220, 220),
    ]

    CLOTHING_COLORS = [
        (60, 60, 80),
        (80, 60, 60),
        (60, 80, 60),
        (70, 70, 70),
        (100, 80, 60),
        (90, 90, 110),
    ]

    BG_COLORS = [
        (200, 220, 240),
        (240, 240, 240),
        (220, 240, 220),
        (255, 255, 255),
    ]

    @classmethod
    def generate(
        cls,
        size: Tuple[int, int] = (500, 670),
        gender: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> Image.Image:
        """Generate a random avatar image."""
        if seed is not None:
            random.seed(seed)

        if gender not in ["male", "female"]:
            gender = random.choice(["male", "female"])

        bg_color = random.choice(cls.BG_COLORS)
        img = Image.new("RGB", size, bg_color)
        draw = ImageDraw.Draw(img)

        skin_tone = random.choice(cls.SKIN_TONES)
        hair_color = random.choice(cls.HAIR_COLORS)
        clothing_color = random.choice(cls.CLOTHING_COLORS)

        width, height = size
        center_x = width // 2

        neck_width = width // 5
        neck_height = height // 8
        neck_top = height * 6 // 10
        draw.rectangle(
            [
                center_x - neck_width // 2,
                neck_top,
                center_x + neck_width // 2,
                neck_top + neck_height,
            ],
            fill=skin_tone,
        )

        shoulder_width = width * 3 // 4
        shoulder_y = neck_top + neck_height - 10
        draw.polygon(
            [
                (center_x - shoulder_width // 2, height),
                (center_x - width // 6, shoulder_y),
                (center_x + width // 6, shoulder_y),
                (center_x + shoulder_width // 2, height),
            ],
            fill=clothing_color,
        )

        collar_width = width // 4
        collar_height = height // 15
        draw.polygon(
            [
                (center_x - collar_width // 2, shoulder_y),
                (center_x, shoulder_y + collar_height),
                (center_x + collar_width // 2, shoulder_y),
            ],
            fill=(
                clothing_color[0] + 20,
                clothing_color[1] + 20,
                clothing_color[2] + 20,
            ),
        )

        face_width = width // 3
        face_height = height // 3
        face_top = height // 6
        face_bbox = [
            center_x - face_width // 2,
            face_top,
            center_x + face_width // 2,
            face_top + face_height,
        ]
        draw.ellipse(face_bbox, fill=skin_tone)

        cls._draw_hair(
            draw, center_x, face_top, face_width, face_height, hair_color, gender
        )
        cls._draw_face_features(
            draw, center_x, face_top, face_width, face_height, skin_tone, gender
        )

        img = cls._add_texture(img)

        return img

    @classmethod
    def _draw_hair(
        cls,
        draw: ImageDraw.Draw,
        center_x: int,
        face_top: int,
        face_width: int,
        face_height: int,
        hair_color: Tuple[int, int, int],
        gender: str,
    ) -> None:
        """Draw hair on the avatar."""
        hair_height = face_height // 3
        hair_top = face_top - hair_height // 2
        hair_bbox = [
            center_x - face_width // 2 - 10,
            hair_top,
            center_x + face_width // 2 + 10,
            face_top + face_height // 4,
        ]
        draw.ellipse(hair_bbox, fill=hair_color)

        side_hair_width = face_width // 8
        if gender == "female":
            hair_length = face_height
            draw.rectangle(
                [
                    center_x - face_width // 2 - side_hair_width,
                    hair_top,
                    center_x - face_width // 2,
                    face_top + hair_length,
                ],
                fill=hair_color,
            )
            draw.rectangle(
                [
                    center_x + face_width // 2,
                    hair_top,
                    center_x + face_width // 2 + side_hair_width,
                    face_top + hair_length,
                ],
                fill=hair_color,
            )
        else:
            draw.rectangle(
                [
                    center_x - face_width // 2 - side_hair_width // 2,
                    hair_top,
                    center_x - face_width // 2,
                    face_top + face_height // 2,
                ],
                fill=hair_color,
            )
            draw.rectangle(
                [
                    center_x + face_width // 2,
                    hair_top,
                    center_x + face_width // 2 + side_hair_width // 2,
                    face_top + face_height // 2,
                ],
                fill=hair_color,
            )

    @classmethod
    def _draw_face_features(
        cls,
        draw: ImageDraw.Draw,
        center_x: int,
        face_top: int,
        face_width: int,
        face_height: int,
        skin_tone: Tuple[int, int, int],
        gender: str,
    ) -> None:
        """Draw facial features (eyes, nose, mouth)."""
        eye_y = face_top + face_height // 3
        eye_offset = face_width // 5
        eye_size = face_width // 12
        eye_color = (40, 30, 30)

        for offset in [-eye_offset, eye_offset]:
            eye_x = center_x + offset
            draw.ellipse(
                [
                    eye_x - eye_size // 2,
                    eye_y - eye_size // 3,
                    eye_x + eye_size // 2,
                    eye_y + eye_size // 3,
                ],
                fill=eye_color,
            )

        eyebrow_y = eye_y - face_height // 8
        eyebrow_length = face_width // 6
        eyebrow_thickness = max(2, face_height // 30)
        eyebrow_color = random.choice(cls.HAIR_COLORS[:4])

        for offset in [-eye_offset, eye_offset]:
            eyebrow_x = center_x + offset
            draw.line(
                [
                    (eyebrow_x - eyebrow_length // 2, eyebrow_y),
                    (eyebrow_x + eyebrow_length // 2, eyebrow_y),
                ],
                fill=eyebrow_color,
                width=eyebrow_thickness,
            )

        nose_y = face_top + face_height // 2
        nose_length = face_height // 6
        draw.line(
            [
                (center_x, nose_y),
                (center_x, nose_y + nose_length),
            ],
            fill=(skin_tone[0] - 20, skin_tone[1] - 20, skin_tone[2] - 20),
            width=max(2, face_width // 25),
        )

        mouth_y = face_top + face_height * 2 // 3
        mouth_width = face_width // 4
        mouth_color = (180, 100, 100)

        draw.arc(
            [
                center_x - mouth_width // 2,
                mouth_y - face_height // 12,
                center_x + mouth_width // 2,
                mouth_y + face_height // 12,
            ],
            start=0,
            end=180,
            fill=mouth_color,
            width=max(2, face_height // 25),
        )

    @classmethod
    def _add_texture(cls, img: Image.Image) -> Image.Image:
        """Add subtle texture/noise to the image for realism."""
        img_array = np.array(img)
        noise = np.random.normal(0, 3, img_array.shape).astype(np.int16)
        img_array = np.clip(img_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(img_array)


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
        self._fonts: dict = {}
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
            return font
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
    ) -> Image.Image:
        """Generate an ID card image from an Identity object.

        Uses the original template and layout from the reference implementation.
        """
        im = self._get_template()

        if include_avatar:
            avatar = AvatarGenerator.generate(
                size=(500, 670),
                gender=identity.gender,
                seed=avatar_seed,
            )
            avatar = avatar.resize((500, 670)).convert("RGBA")
            im.paste(avatar, (1500, 690), mask=avatar)

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
    ) -> list[Path]:
        """Generate ID card images for multiple identities."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_paths = []

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
) -> Image.Image:
    """Convenience function to generate a single ID card image."""
    generator = IDCardImageGenerator()
    return generator.generate(
        identity=identity,
        output_path=output_path,
        include_avatar=include_avatar,
        avatar_seed=seed,
    )
