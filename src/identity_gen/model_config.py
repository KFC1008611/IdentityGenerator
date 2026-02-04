"""Model configuration management for diffusers-based avatar generation."""

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default models available for selection
DEFAULT_MODELS = {
    "tiny-sd": {
        "repo_id": "segmind/tiny-sd",
        "name": "Tiny Stable Diffusion",
        "description": "轻量级 Stable Diffusion (~1GB)，生成速度快",
        "size_gb": 1.0,
        "recommended": True,
        "prompt_template": "professional passport photo of asian {gender}, centered face, symmetrical features, clear eyes, natural skin texture, front view, neutral expression, looking directly at camera, pure white background, studio lighting, photorealistic, high quality, 8k uhd, sharp focus on face, proper face proportions",
        "negative_prompt": "cartoon, anime, painting, illustration, 3d render, sculpture, (worst quality, low quality, normal quality:1.4), blurry, out of focus, side view, profile, sunglasses, hat, beard, mustache, distorted face, deformed features, ugly, disfigured, poorly drawn face, mutation, mutated, extra limbs, extra fingers, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck, cross-eyed, mutated hands, polar lowres, bad face",
        "guidance_scale": 8.5,
        "num_inference_steps": 30,
    },
    "small-sd": {
        "repo_id": "segmind/small-sd",
        "name": "Small Stable Diffusion",
        "description": "小型 Stable Diffusion (~1.5GB)，质量较好",
        "size_gb": 1.5,
        "recommended": False,
        "prompt_template": "professional passport photo of asian {gender}, centered face, symmetrical features, clear eyes, natural skin texture, front view, neutral expression, looking directly at camera, pure white background, studio lighting, photorealistic, high quality, 8k uhd, sharp focus on face, proper face proportions",
        "negative_prompt": "cartoon, anime, painting, illustration, 3d render, sculpture, (worst quality, low quality, normal quality:1.4), blurry, out of focus, side view, profile, sunglasses, hat, beard, mustache, distorted face, deformed features, ugly, disfigured, poorly drawn face, mutation, mutated, extra limbs, extra fingers, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck, cross-eyed, mutated hands, polar lowres, bad face",
        "guidance_scale": 8.5,
        "num_inference_steps": 35,
    },
    "realistic-vision": {
        "repo_id": "SG161222/Realistic_Vision_V5.1_noVAE",
        "name": "Realistic Vision",
        "description": "写实风格模型 (~4GB)，质量最高但较慢",
        "size_gb": 4.0,
        "recommended": False,
        "prompt_template": "professional passport photo of asian {gender}, centered face, symmetrical features, clear eyes, natural skin texture with visible pores, front view, neutral expression, looking directly at camera, pure white background, studio lighting, photorealistic, high quality, 8k uhd, sharp focus on face, proper face proportions, lifelike",
        "negative_prompt": "cartoon, anime, painting, illustration, 3d render, sculpture, (worst quality, low quality, normal quality:1.4), blurry, out of focus, side view, profile, sunglasses, hat, beard, mustache, distorted face, deformed features, ugly, disfigured, poorly drawn face, mutation, mutated, extra limbs, extra fingers, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck, cross-eyed, mutated hands, polar lowres, bad face, plastic skin, doll-like, artificial",
        "guidance_scale": 8.0,
        "num_inference_steps": 40,
    },
}


@dataclass
class ModelConfig:
    """Configuration for a diffusion model."""

    repo_id: str
    name: str
    description: str
    size_gb: float
    prompt_template: str
    negative_prompt: str
    guidance_scale: float
    num_inference_steps: int
    custom: bool = False  # True if user added custom model
    recommended: bool = False  # Whether this model is recommended for new users

    def format_prompt(self, gender: str = "person") -> str:
        """Format the prompt template with gender."""
        gender_map = {
            "male": "man",
            "female": "woman",
            "man": "man",
            "woman": "woman",
            "boy": "boy",
            "girl": "girl",
        }
        gender_en = gender_map.get(gender.lower(), "person")
        return self.prompt_template.format(gender=gender_en)


class ModelConfigManager:
    """Manages model configuration and storage."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize the model config manager.

        Args:
            config_dir: Directory to store configuration. Defaults to ~/.identity_gen
        """
        if config_dir is None:
            self.config_dir = Path.home() / ".identity_gen"
        else:
            self.config_dir = Path(config_dir)

        self.config_file = self.config_dir / "model_config.json"
        self.cache_dir = self.config_dir / "models"

        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._config = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from file or create default."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}, using defaults")

        # Default configuration
        return {
            "selected_model": None,  # None means not configured yet
            "custom_models": {},
            "cache_dir": str(self.cache_dir),
        }

    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def get_model_dir(self, model_key: str) -> Path:
        """Get the cache directory for a specific model."""
        return self.cache_dir / model_key.replace("/", "--")

    def is_model_downloaded(self, model_key: str) -> bool:
        """Check if a model is already downloaded."""
        model_dir = self.get_model_dir(model_key)
        if not model_dir.exists():
            return False

        # Check for essential model files
        essential_files = [
            "model_index.json",
            "unet/diffusion_pytorch_model.bin",
            "text_encoder/model.safetensors",
        ]

        for file in essential_files:
            if (model_dir / file).exists():
                return True

        return False

    def get_model_config(self, model_key: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model."""
        # Check default models
        if model_key in DEFAULT_MODELS:
            data = DEFAULT_MODELS[model_key].copy()
            return ModelConfig(**data)

        # Check custom models
        if model_key in self._config.get("custom_models", {}):
            data = self._config["custom_models"][model_key]
            return ModelConfig(custom=True, **data)

        return None

    def list_available_models(self) -> dict[str, ModelConfig]:
        """List all available models (default + custom)."""
        models = {}

        # Add default models
        for key, data in DEFAULT_MODELS.items():
            models[key] = ModelConfig(**data)

        # Add custom models
        for key, data in self._config.get("custom_models", {}).items():
            models[key] = ModelConfig(custom=True, **data)

        return models

    def get_selected_model(self) -> Optional[tuple[str, ModelConfig]]:
        """Get the currently selected model."""
        selected = self._config.get("selected_model")
        if selected is None:
            return None

        config = self.get_model_config(selected)
        if config is None:
            return None

        return selected, config

    def set_selected_model(self, model_key: str) -> bool:
        """Set the selected model."""
        if model_key not in DEFAULT_MODELS and model_key not in self._config.get(
            "custom_models", {}
        ):
            return False

        self._config["selected_model"] = model_key
        self._save_config()
        return True

    def add_custom_model(
        self,
        key: str,
        repo_id: str,
        name: str,
        description: str,
        size_gb: float,
        prompt_template: str,
        negative_prompt: str = "",
        guidance_scale: float = 7.5,
        num_inference_steps: int = 20,
    ) -> bool:
        """Add a custom model configuration."""
        if key in DEFAULT_MODELS:
            logger.error(f"Cannot override default model: {key}")
            return False

        self._config["custom_models"][key] = {
            "repo_id": repo_id,
            "name": name,
            "description": description,
            "size_gb": size_gb,
            "prompt_template": prompt_template,
            "negative_prompt": negative_prompt,
            "guidance_scale": guidance_scale,
            "num_inference_steps": num_inference_steps,
        }
        self._save_config()
        return True

    def remove_custom_model(self, key: str) -> bool:
        """Remove a custom model configuration."""
        if key in self._config.get("custom_models", {}):
            del self._config["custom_models"][key]

            # If this was the selected model, reset selection
            if self._config.get("selected_model") == key:
                self._config["selected_model"] = None

            self._save_config()
            return True
        return False

    def get_cache_dir(self) -> Path:
        """Get the models cache directory."""
        return self.cache_dir

    def is_configured(self) -> bool:
        """Check if a model has been selected and is ready to use."""
        selected = self._config.get("selected_model")
        if selected is None:
            return False

        return self.is_model_downloaded(selected)

    def reset_configuration(self) -> None:
        """Reset the configuration (useful for testing or starting over)."""
        self._config["selected_model"] = None
        self._save_config()


# Global config manager instance
_config_manager: Optional[ModelConfigManager] = None


def get_config_manager() -> ModelConfigManager:
    """Get the global config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ModelConfigManager()
    return _config_manager
