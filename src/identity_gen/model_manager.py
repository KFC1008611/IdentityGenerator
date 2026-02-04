"""Model manager for downloading and loading diffusion models."""

import logging
from pathlib import Path
from typing import Any, Callable, Optional

from .model_config import ModelConfig, get_config_manager

logger = logging.getLogger(__name__)

# Global pipeline cache
_pipeline_cache: dict[str, Any] = {}


class ModelManager:
    """Manages diffusion model downloading and loading."""

    def __init__(self):
        """Initialize the model manager."""
        self.config_manager = get_config_manager()

    def is_model_available(self, model_key: Optional[str] = None) -> bool:
        """Check if a model is available (downloaded).

        Args:
            model_key: Model key to check. If None, checks the selected model.

        Returns:
            True if model is available.
        """
        if model_key is None:
            selected = self.config_manager.get_selected_model()
            if selected is None:
                return False
            model_key = selected[0]

        return self.config_manager.is_model_downloaded(model_key)

    def download_model(
        self,
        model_key: str,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> bool:
        """Download a model from Hugging Face.

        Args:
            model_key: Key of the model to download.
            progress_callback: Optional callback function(progress: float) for progress updates.

        Returns:
            True if download was successful.
        """
        config = self.config_manager.get_model_config(model_key)
        if config is None:
            logger.error(f"Unknown model: {model_key}")
            return False

        try:
            from huggingface_hub import snapshot_download

            cache_dir = self.config_manager.get_model_dir(model_key)

            logger.info(f"Downloading model {model_key} ({config.name})...")
            logger.info(f"Repository: {config.repo_id}")
            logger.info(f"Estimated size: {config.size_gb:.1f} GB")
            logger.info(f"Cache directory: {cache_dir}")

            # Download the model
            # Use snapshot_download for better control
            snapshot_download(
                repo_id=config.repo_id,
                local_dir=str(cache_dir),
            )

            logger.info(f"Model {model_key} downloaded successfully!")
            return True

        except ImportError as e:
            logger.error(f"Required libraries not installed: {e}")
            logger.error("Please install: pip install diffusers huggingface-hub")
            return False

        except Exception as e:
            logger.error(f"Failed to download model {model_key}: {e}")
            return False

    def load_pipeline(
        self,
        model_key: Optional[str] = None,
        device: str = "auto",
    ) -> Optional[Any]:
        """Load a diffusion pipeline for the specified model.

        Args:
            model_key: Model key to load. If None, loads the selected model.
            device: Device to load model on ("auto", "cpu", "cuda", "mps").

        Returns:
            Loaded DiffusionPipeline or None if loading failed.
        """
        if model_key is None:
            selected = self.config_manager.get_selected_model()
            if selected is None:
                logger.error("No model selected. Please configure a model first.")
                return None
            model_key, config = selected
        else:
            config = self.config_manager.get_model_config(model_key)
            if config is None:
                logger.error(f"Unknown model: {model_key}")
                return None

        # Check if already cached
        if model_key in _pipeline_cache:
            logger.debug(f"Using cached pipeline for {model_key}")
            return _pipeline_cache[model_key]

        # Check if model is downloaded
        if not self.config_manager.is_model_downloaded(model_key):
            logger.error(f"Model {model_key} not downloaded. Please download it first.")
            return None

        try:
            import torch
            from diffusers.pipelines.stable_diffusion.pipeline_stable_diffusion import (
                StableDiffusionPipeline,
            )

            cache_dir = self.config_manager.get_model_dir(model_key)

            logger.info(f"Loading model {model_key} ({config.name})...")

            # Determine device
            if device == "auto":
                if torch.cuda.is_available():
                    device = "cuda"
                elif torch.backends.mps.is_available():
                    # MPS 有兼容性问题，直接使用 CPU
                    logger.warning(
                        "MPS backend has compatibility issues, using CPU instead"
                    )
                    device = "cpu"
                else:
                    device = "cpu"

            logger.info(f"Using device: {device}")

            # Load pipeline
            # Check if local model_index.json exists (downloaded model)
            model_index = cache_dir / "model_index.json"

            # MPS 对 float16 支持不完善，强制使用 float32
            use_float32 = device in ("cpu", "mps")
            torch_dtype = torch.float32 if use_float32 else torch.float16

            # Load kwargs
            load_kwargs = {
                "torch_dtype": torch_dtype,
                "safety_checker": None,
                "requires_safety_checker": False,
            }

            try:
                if model_index.exists():
                    # Load from local cache using StableDiffusionPipeline
                    pipeline = StableDiffusionPipeline.from_pretrained(
                        str(cache_dir), **load_kwargs
                    )
                else:
                    # Load from Hugging Face (should not happen if downloaded correctly)
                    logger.warning(
                        f"Local model not found, loading from Hugging Face..."
                    )
                    pipeline = StableDiffusionPipeline.from_pretrained(
                        config.repo_id,
                        cache_dir=str(self.config_manager.get_cache_dir()),
                        **load_kwargs,
                    )
            except Exception as load_error:
                # Handle specific error: 'super' object has no attribute '__getattr__'
                error_msg = str(load_error)
                if "__getattr__" in error_msg or "super" in error_msg:
                    logger.warning(
                        f"Standard loading failed ({error_msg}), trying alternative..."
                    )
                    try:
                        # Try with local_files_only to avoid network issues
                        if model_index.exists():
                            pipeline = StableDiffusionPipeline.from_pretrained(
                                str(cache_dir), local_files_only=True, **load_kwargs
                            )
                        else:
                            raise load_error
                    except Exception:
                        logger.error("Alternative loading also failed")
                        raise load_error
                else:
                    raise load_error

            pipeline = pipeline.to(device)

            if hasattr(pipeline, "enable_attention_slicing"):
                pipeline.enable_attention_slicing()

            if device == "cpu" and hasattr(pipeline, "enable_sequential_cpu_offload"):
                pipeline.enable_sequential_cpu_offload()

            # Cache the pipeline
            _pipeline_cache[model_key] = pipeline

            logger.info(f"Model {model_key} loaded successfully!")
            return pipeline

        except ImportError as e:
            logger.error(f"Required libraries not installed: {e}")
            logger.error("Please install: pip install diffusers torch")
            return None

        except Exception as e:
            logger.error(f"Failed to load model {model_key}: {e}")
            logger.error(
                "This may be due to version incompatibility between diffusers, transformers, and torch."
            )
            logger.error(
                "Try: pip install --upgrade diffusers transformers torch accelerate"
            )
            return None

    def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        guidance_scale: float = 7.5,
        num_inference_steps: int = 20,
        seed: Optional[int] = None,
        height: int = 512,
        width: int = 512,
        model_key: Optional[str] = None,
    ) -> Optional[Any]:
        """Generate an image using the loaded model.

        Args:
            prompt: Text prompt for generation.
            negative_prompt: Negative prompt to avoid certain features.
            guidance_scale: Guidance scale for classifier-free guidance.
            num_inference_steps: Number of denoising steps.
            seed: Random seed for reproducibility.
            height: Image height.
            width: Image width.
            model_key: Model to use. If None, uses the selected model.

        Returns:
            Generated PIL Image or None if generation failed.
        """
        pipeline = self.load_pipeline(model_key)
        if pipeline is None:
            return None

        try:
            import torch

            # Set seed for reproducibility
            generator = None
            if seed is not None:
                device = str(pipeline.device)
                # Handle meta device (model not properly loaded on accelerator)
                if device == "meta" or not device or device == "None":
                    device = "cpu"
                try:
                    generator = torch.Generator(device=device).manual_seed(seed)
                except RuntimeError as gen_error:
                    logger.warning(
                        f"Failed to create generator on {device}: {gen_error}"
                    )
                    generator = torch.Generator("cpu").manual_seed(seed)

            # Generate image
            result = pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                generator=generator,
                height=height,
                width=width,
            )

            return result.images[0]

        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return None

    def clear_cache(self) -> None:
        """Clear the pipeline cache to free memory."""
        global _pipeline_cache
        _pipeline_cache.clear()
        logger.info("Pipeline cache cleared")

    def delete_model(self, model_key: str) -> bool:
        """Delete a downloaded model to free disk space.

        Args:
            model_key: Model to delete.

        Returns:
            True if deletion was successful.
        """
        model_dir = self.config_manager.get_model_dir(model_key)

        if not model_dir.exists():
            logger.warning(f"Model {model_key} not found at {model_dir}")
            return False

        try:
            import shutil

            # Remove from cache if loaded
            if model_key in _pipeline_cache:
                del _pipeline_cache[model_key]

            # Delete model directory
            shutil.rmtree(model_dir)

            logger.info(f"Model {model_key} deleted successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to delete model {model_key}: {e}")
            return False

    def get_model_info(self, model_key: str) -> Optional[dict[str, Any]]:
        """Get information about a model.

        Args:
            model_key: Model to get info for.

        Returns:
            Dictionary with model information.
        """
        config = self.config_manager.get_model_config(model_key)
        if config is None:
            return None

        is_downloaded = self.config_manager.is_model_downloaded(model_key)
        model_dir = self.config_manager.get_model_dir(model_key)

        # Calculate actual size if downloaded
        actual_size_mb = 0
        if is_downloaded and model_dir.exists():
            try:
                actual_size_mb = sum(
                    f.stat().st_size for f in model_dir.rglob("*") if f.is_file()
                ) / (1024 * 1024)
            except:
                pass

        return {
            "key": model_key,
            "name": config.name,
            "description": config.description,
            "repo_id": config.repo_id,
            "estimated_size_gb": config.size_gb,
            "actual_size_mb": actual_size_mb,
            "is_downloaded": is_downloaded,
            "is_cached": model_key in _pipeline_cache,
            "cache_dir": str(model_dir),
        }


# Global model manager instance
_model_manager: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """Get the global model manager instance."""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager
