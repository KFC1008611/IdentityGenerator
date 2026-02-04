"""CLI entry point for identity generator."""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .generator import IdentityGenerator
from .models import IdentityConfig, IdentityField, OutputFormat
from .formatters import IdentityFormatter
from .idcard_image_generator import IDCardImageGenerator

console = Console()
logger = logging.getLogger(__name__)

LOGO = """
╦╔╦╗╔═╗╔═╗╦  ╔═╗  ╔═╗╔╗╔╔╦╗
║║║║╠═╝║ ║║  ╚═╗  ║ ╦║║║ ║ 
╩╩ ╩╩  ╚═╝╩═╝╚═╝  ╚═╝╝╚╝ ╩ 
"""


def setup_logging(verbose: bool) -> None:
    """Setup logging configuration."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def detect_format_from_extension(filename: str) -> Optional[OutputFormat]:
    """Detect output format from file extension.

    Args:
        filename: The filename to check.

    Returns:
        OutputFormat if extension is recognized, None otherwise.
    """
    ext = filename.lower().split(".")[-1] if "." in filename else ""

    format_map = {
        "json": OutputFormat.JSON,
        "csv": OutputFormat.CSV,
        "txt": OutputFormat.TABLE,
        "text": OutputFormat.TABLE,
        "sql": OutputFormat.SQL,
        "md": OutputFormat.MARKDOWN,
        "markdown": OutputFormat.MARKDOWN,
        "yaml": OutputFormat.YAML,
        "yml": OutputFormat.YAML,
        "vcf": OutputFormat.VCARD,
        "vcard": OutputFormat.VCARD,
    }

    return format_map.get(ext)


def generate_default_filename(output_format: OutputFormat = OutputFormat.CSV) -> str:
    """Generate default filename based on format and timestamp.

    Args:
        output_format: The output format. Defaults to CSV.

    Returns:
        Generated filename with appropriate extension.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    extensions = {
        OutputFormat.JSON: "json",
        OutputFormat.CSV: "csv",
        OutputFormat.TABLE: "txt",
        OutputFormat.RAW: "txt",
        OutputFormat.SQL: "sql",
        OutputFormat.MARKDOWN: "md",
        OutputFormat.YAML: "yaml",
        OutputFormat.VCARD: "vcf",
    }
    ext = extensions.get(output_format, "csv")
    return f"identities_{timestamp}.{ext}"


def _prompt_avatar_backend() -> tuple[str, bool]:
    if not sys.stdin.isatty():
        logger.info("Non-interactive mode detected, using auto avatar backend")
        return "auto", True

    click.echo("\n请选择头像生成方式：")
    click.echo("  1. AI 模型 (diffusers)")
    click.echo("  2. 火山方舟 (ARK)")
    click.echo("  3. random_face")
    click.echo("  4. 备用剪影")
    click.echo("  5. 不生成头像")

    choice = click.prompt(
        "请选择 (1-5)",
        type=click.Choice(["1", "2", "3", "4", "5"], case_sensitive=False),
        default="1",
        show_default=True,
    )

    if choice == "1":
        return "diffusers", True
    if choice == "2":
        return "ark", True
    if choice == "3":
        return "random_face", True
    if choice == "4":
        return "fallback", True
    return "auto", False


@click.group(invoke_without_command=True)
@click.option(
    "--locale",
    "-l",
    default="zh_CN",
    help="Locale for generation (China only)",
    show_default=True,
)
@click.option(
    "--count",
    "-n",
    default=1,
    type=int,
    help="Number of identities to generate",
    show_default=True,
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(
        ["json", "csv", "table", "raw", "sql", "markdown", "yaml", "vcard"],
        case_sensitive=False,
    ),
    default=None,
    help="Output format (default: auto-detect from file extension, or csv if not specified)",
    show_default=False,
)
@click.option(
    "--output",
    "-o",
    help="Output file path (default: auto-generated)",
)
@click.option(
    "--stdout",
    is_flag=True,
    help="Output to stdout instead of file",
)
@click.option(
    "--include",
    "-i",
    multiple=True,
    help="Fields to include (can be used multiple times)",
)
@click.option(
    "--exclude",
    "-e",
    multiple=True,
    help="Fields to exclude (can be used multiple times)",
)
@click.option(
    "--seed",
    "-s",
    type=int,
    help="Random seed for reproducible generation",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
@click.option(
    "--idcard/--no-idcard",
    default=True,
    help="Generate ID card images along with text data (default: enabled)",
    show_default=True,
)
@click.option(
    "--idcard-dir",
    default="idcards",
    help="Output directory for ID card images",
    show_default=True,
)
@click.option(
    "--idcard-no-avatar",
    is_flag=True,
    help="Generate ID cards without avatars",
)
@click.pass_context
def cli(
    ctx: click.Context,
    locale: str,
    count: int,
    output_format: str,
    output: Optional[str],
    stdout: bool,
    include: tuple,
    exclude: tuple,
    seed: Optional[int],
    verbose: bool,
    idcard: bool,
    idcard_dir: str,
    idcard_no_avatar: bool,
) -> None:
    """Chinese Identity Generator CLI.

    Generate realistic Chinese virtual identity information and save to files.
    Terminal output is always in log format.
    """
    setup_logging(verbose)

    # Print logo for main command
    if ctx.invoked_subcommand is None:
        console.print(Text(LOGO, style="bold cyan"))

    # If no subcommand, run default generation
    if ctx.invoked_subcommand is None:
        try:
            # Determine output path
            if stdout:
                output_path = None
                logger.info("Output mode: stdout")
            elif output:
                output_path = output
                logger.info(f"Output file: {output_path}")
            else:
                output_path = generate_default_filename()
                logger.info(f"Output file: {output_path} (auto-generated)")

            # Determine output format (priority: --format > file extension > default csv)
            fmt: OutputFormat
            if output_format:
                fmt = OutputFormat(output_format.lower())
                logger.info(f"Format: {fmt.value} (from --format)")
            elif output:
                detected = detect_format_from_extension(output)
                if detected:
                    fmt = detected
                    logger.info(f"Format: {fmt.value} (auto-detected)")
                else:
                    fmt = OutputFormat.CSV
                    logger.info(
                        f"Format: {fmt.value} (default, unrecognized extension)"
                    )
            else:
                fmt = OutputFormat.CSV
                logger.info(f"Format: {fmt.value} (default)")

            logger.info(f"Starting identity generation")
            logger.info(f"  Locale: {locale}")
            logger.info(f"  Count: {count}")
            if seed:
                logger.info(f"  Seed: {seed}")
            if include:
                logger.info(f"  Include fields: {', '.join(include)}")
            if exclude:
                logger.info(f"  Exclude fields: {', '.join(exclude)}")
            include_avatar = not idcard_no_avatar
            avatar_backend = "auto"
            if idcard and not stdout and include_avatar:
                avatar_backend, include_avatar = _prompt_avatar_backend()
            if idcard and not stdout:
                logger.info("  Generate ID cards: enabled")
                logger.info(f"  ID card directory: {idcard_dir}")
                if include_avatar:
                    logger.info(f"  ID card avatar backend: {avatar_backend}")
                else:
                    logger.info("  ID card avatars: disabled")

            config = IdentityConfig(
                locale=locale,
                count=count,
                include_fields=list(include) if include else None,
                exclude_fields=list(exclude) if exclude else None,
                seed=seed,
                format=fmt,
            )

            logger.info("Generating identities...")
            generator = IdentityGenerator(config)
            identities = generator.generate_batch()
            logger.info(f"Generated {len(identities)} identities")

            logger.info("Formatting output...")
            formatter = IdentityFormatter()
            formatted = formatter.format(
                identities,
                config.format,
                config.get_effective_fields(),
            )

            if output_path:
                # Save to file
                formatter.write_output(formatted, output_path)
                abs_path = os.path.abspath(output_path)
                logger.info(f"✓ Successfully saved to: {abs_path}")

                # Display file size
                file_size = os.path.getsize(output_path)
                if file_size < 1024:
                    size_str = f"{file_size} bytes"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                else:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
                logger.info(f"  File size: {size_str}")

                # Generate ID card images if enabled
                if idcard:
                    logger.info("Generating ID card images...")
                    idcard_output = Path(idcard_dir)
                    idcard_output.mkdir(parents=True, exist_ok=True)

                    idcard_generator = IDCardImageGenerator()

                    # Create filename pattern based on output filename
                    base_name = Path(output_path).stem
                    pattern = f"{base_name}_{{index:04d}}.png"

                    saved_files = idcard_generator.generate_batch(
                        identities=identities,
                        output_dir=idcard_output,
                        filename_pattern=pattern,
                        include_avatar=include_avatar,
                        avatar_backend=avatar_backend,
                    )

                    logger.info(
                        f"✓ Successfully generated {len(saved_files)} ID card image(s)"
                    )
                    for file_path in saved_files[:5]:  # Show first 5
                        logger.info(f"  - {file_path}")
                    if len(saved_files) > 5:
                        logger.info(f"  ... and {len(saved_files) - 5} more")
            else:
                # Output to stdout
                print(formatted)

            logger.info("Done!")

        except Exception as e:
            logger.error(f"Error: {e}")
            if verbose:
                logger.exception("Full traceback:")
            sys.exit(1)


@cli.command()
def fields() -> None:
    """List all available identity fields."""
    console.print("\n[bold cyan]Available Identity Fields:[/bold cyan]\n")

    field_groups = {
        "Personal (基础信息)": [
            "name",
            "first_name",
            "last_name",
            "gender",
            "birthdate",
            "ssn",
            "ethnicity",
            "blood_type",
            "height",
            "weight",
        ],
        "Contact (联系方式)": [
            "email",
            "phone",
            "address",
            "city",
            "state",
            "zipcode",
            "country",
        ],
        "Professional (职业信息)": ["company", "job_title", "education", "major"],
        "Account (账户信息)": ["username", "password", "wechat_id", "qq_number"],
        "Social (社会信息)": ["political_status", "marital_status", "religion"],
        "Finance (财务信息)": ["bank_card", "license_plate", "social_credit_code"],
        "Digital (数字身份)": ["ip_address", "mac_address"],
        "Astrological (生辰信息)": ["zodiac_sign", "chinese_zodiac"],
        "Additional (其他信息)": ["emergency_contact", "emergency_phone", "hobbies"],
    }

    for group, fields_list in field_groups.items():
        console.print(f"[bold]{group}:[/bold]")
        for field in fields_list:
            console.print(f"  • {field}")
        console.print()


@cli.command()
def locales() -> None:
    """List supported locale (China only)."""
    console.print("\n[bold cyan]Supported Locale:[/bold cyan]\n")
    console.print("[bold]zh_CN[/bold] - Chinese (China)")
    console.print("\n[dim]Note: This tool generates Chinese identities only.[/dim]")


@cli.command()
@click.option(
    "--locale",
    "-l",
    default="en_US",
    help="Locale for preview",
)
def preview(locale: str) -> None:
    """Generate a sample identity for preview."""
    # Force zh_CN locale for preview
    config = IdentityConfig(locale="zh_CN", count=1, format=OutputFormat.TABLE)
    generator = IdentityGenerator(config)
    identity = generator.generate()

    console.print(f"\n[bold cyan]Sample Chinese Identity:[/bold cyan]\n")

    data = identity.to_dict()
    for key, value in data.items():
        if value is not None:
            console.print(f"[bold]{key.replace('_', ' ').title()}:[/bold] {value}")


@cli.command(name="generate-idcard")
@click.option(
    "--count",
    "-n",
    default=1,
    type=int,
    help="Number of ID cards to generate",
    show_default=True,
)
@click.option(
    "--output-dir",
    "-o",
    default="idcards",
    help="Output directory for ID card images",
    show_default=True,
)
@click.option(
    "--include-avatar",
    is_flag=True,
    default=True,
    help="Include avatar image on ID card",
)
@click.option(
    "--no-avatar",
    is_flag=True,
    help="Generate ID card without avatar",
)
@click.option(
    "--seed",
    "-s",
    type=int,
    help="Random seed for reproducible generation",
)
@click.option(
    "--filename-pattern",
    "-f",
    default="{name}_idcard.png",
    help="Filename pattern (available placeholders: {name}, {ssn}, {index})",
    show_default=True,
)
def generate_idcard(
    count: int,
    output_dir: str,
    include_avatar: bool,
    no_avatar: bool,
    seed: Optional[int],
    filename_pattern: str,
) -> None:
    """Generate Chinese ID card images.

    Generates realistic Chinese ID card images with random avatars.
    Images are saved as PNG files in the specified output directory.
    """
    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if no_avatar:
            include_avatar = False

        avatar_backend = "auto"
        if include_avatar:
            avatar_backend, include_avatar = _prompt_avatar_backend()

        logger.info(f"Generating {count} ID card image(s)")
        logger.info(f"Output directory: {output_path.absolute()}")
        logger.info(f"Include avatar: {include_avatar}")
        if include_avatar:
            logger.info(f"Avatar backend: {avatar_backend}")
        if seed:
            logger.info(f"Random seed: {seed}")

        config = IdentityConfig(
            locale="zh_CN",
            count=count,
            seed=seed,
            include_fields=[
                "name",
                "gender",
                "ethnicity",
                "birthdate",
                "address",
                "ssn",
            ],
        )

        logger.info("Generating identity data...")
        generator = IdentityGenerator(config)
        identities = generator.generate_batch()

        logger.info("Generating ID card images...")
        idcard_generator = IDCardImageGenerator()

        saved_files = idcard_generator.generate_batch(
            identities=identities,
            output_dir=output_path,
            filename_pattern=filename_pattern,
            include_avatar=include_avatar,
            avatar_backend=avatar_backend,
        )

        logger.info(f"✓ Successfully generated {len(saved_files)} ID card image(s)")
        for file_path in saved_files:
            logger.info(f"  - {file_path}")

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


# Model management commands
@cli.group(name="model")
def model_cli() -> None:
    """Manage AI models for avatar generation.

    Commands to list, download, and configure diffusion models
    for high-quality avatar generation.
    """
    pass


@model_cli.command(name="list")
def model_list() -> None:
    """List available diffusion models."""
    try:
        from .model_config import get_config_manager, DEFAULT_MODELS
        from .model_manager import get_model_manager

        config_manager = get_config_manager()
        model_manager = get_model_manager()

        console.print("\n[bold cyan]Available Diffusion Models:[/bold cyan]\n")

        selected = config_manager.get_selected_model()
        selected_key = selected[0] if selected else None

        for key, data in DEFAULT_MODELS.items():
            is_selected = key == selected_key
            is_downloaded = config_manager.is_model_downloaded(key)

            status = []
            if is_selected:
                status.append("[bold green]✓ SELECTED[/bold green]")
            if is_downloaded:
                status.append("[green]Downloaded[/green]")

            status_str = (
                " | ".join(status) if status else "[yellow]Not downloaded[/yellow]"
            )

            recommended = (
                "[bold yellow]★ RECOMMENDED[/bold yellow]"
                if data.get("recommended")
                else ""
            )

            console.print(f"[bold]{key}[/bold] {recommended}")
            console.print(f"  Name: {data['name']}")
            console.print(f"  Description: {data['description']}")
            console.print(f"  Size: ~{data['size_gb']} GB")
            console.print(f"  Status: {status_str}")
            console.print()

        if selected_key:
            console.print(f"[green]Currently selected: {selected_key}[/green]")
        else:
            console.print(
                "[yellow]No model selected. Use 'identity-gen model configure' to select one.[/yellow]"
            )

    except Exception as e:
        logger.error(f"Error listing models: {e}")
        sys.exit(1)


@model_cli.command(name="configure")
def model_configure() -> None:
    """Configure and select a model for avatar generation.

    Interactive wizard to select and download a diffusion model.
    """
    try:
        from .model_config import get_config_manager, DEFAULT_MODELS
        from .model_manager import get_model_manager

        config_manager = get_config_manager()
        model_manager = get_model_manager()

        console.print("\n[bold cyan]Model Configuration Wizard[/bold cyan]\n")
        console.print(
            "This wizard will help you select and configure a diffusion model"
        )
        console.print("for high-quality avatar generation.\n")

        # Show available models
        console.print("[bold]Available Models:[/bold]")
        for i, (key, data) in enumerate(DEFAULT_MODELS.items(), 1):
            recommended = (
                "[yellow]★ RECOMMENDED[/yellow]" if data.get("recommended") else ""
            )
            console.print(
                f"  {i}. [bold]{key}[/bold] - {data['name']} (~{data['size_gb']} GB) {recommended}"
            )
            console.print(f"     {data['description']}")
        console.print()

        # Get user choice
        choices = list(DEFAULT_MODELS.keys())
        while True:
            try:
                choice = input("Select a model (1-3) or 'q' to quit: ").strip()
                if choice.lower() == "q":
                    console.print("Configuration cancelled.")
                    return

                idx = int(choice) - 1
                if 0 <= idx < len(choices):
                    selected_key = choices[idx]
                    break
                else:
                    console.print("[red]Invalid choice. Please enter 1-3.[/red]")
            except ValueError:
                console.print("[red]Invalid input. Please enter a number.[/red]")

        selected_model = DEFAULT_MODELS[selected_key]
        console.print(f"\n[green]Selected: {selected_model['name']}[/green]")

        # Check if already downloaded
        if config_manager.is_model_downloaded(selected_key):
            console.print("[green]Model is already downloaded![/green]")
        else:
            console.print(
                f"\n[yellow]Model needs to be downloaded (~{selected_model['size_gb']} GB)[/yellow]"
            )
            download = input("Download now? (y/n): ").strip().lower()

            if download == "y":
                console.print(f"\n[bold]Downloading {selected_model['name']}...[/bold]")
                console.print(
                    "This may take several minutes depending on your connection.\n"
                )

                # Simple progress callback
                def progress_callback(progress):
                    percent = int(progress * 100)
                    console.print(f"Progress: {percent}%", end="\r")

                success = model_manager.download_model(selected_key)

                if success:
                    console.print("\n[green]✓ Download completed successfully![/green]")
                else:
                    console.print(
                        "\n[red]✗ Download failed. Please check your connection and try again.[/red]"
                    )
                    return
            else:
                console.print(
                    "Download skipped. You can download later with 'identity-gen model download'."
                )

        # Set as selected model
        config_manager.set_selected_model(selected_key)
        console.print(
            f"\n[bold green]✓ {selected_model['name']} is now configured for avatar generation![/bold green]"
        )
        console.print(
            "\nYou can now generate ID cards with high-quality avatars using:"
        )
        console.print("  identity-gen --count 1")

    except KeyboardInterrupt:
        console.print("\n\nConfiguration cancelled.")
    except Exception as e:
        logger.error(f"Error configuring model: {e}")
        sys.exit(1)


@model_cli.command(name="download")
@click.argument("model_key")
def model_download(model_key: str) -> None:
    """Download a specific model.

    Args:
        model_key: Key of the model to download (e.g., 'tiny-sd', 'realistic-vision')
    """
    try:
        from .model_config import get_config_manager
        from .model_manager import get_model_manager

        config_manager = get_config_manager()
        model_manager = get_model_manager()

        # Check if model exists
        if model_key not in config_manager.list_available_models():
            console.print(f"[red]Error: Unknown model '{model_key}'[/red]")
            console.print("\nAvailable models:")
            for key in config_manager.list_available_models():
                console.print(f"  - {key}")
            sys.exit(1)

        # Check if already downloaded
        if config_manager.is_model_downloaded(model_key):
            console.print(f"[green]Model '{model_key}' is already downloaded![/green]")
            return

        config = config_manager.get_model_config(model_key)
        if config is None:
            console.print(f"[red]Error: Model '{model_key}' not found[/red]")
            sys.exit(1)

        console.print(f"\n[bold]Downloading {config.name}...[/bold]")
        console.print(f"Size: ~{config.size_gb} GB")
        console.print("This may take several minutes.\n")

        success = model_manager.download_model(model_key)

        if success:
            console.print(f"\n[green]✓ {config.name} downloaded successfully![/green]")
        else:
            console.print(f"\n[red]✗ Failed to download {config.name}[/red]")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error downloading model: {e}")
        sys.exit(1)


@model_cli.command(name="delete")
@click.argument("model_key")
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
def model_delete(model_key: str, force: bool) -> None:
    """Delete a downloaded model to free disk space.

    Args:
        model_key: Key of the model to delete
    """
    try:
        from .model_config import get_config_manager
        from .model_manager import get_model_manager

        config_manager = get_config_manager()
        model_manager = get_model_manager()

        # Check if model is downloaded
        if not config_manager.is_model_downloaded(model_key):
            console.print(f"[yellow]Model '{model_key}' is not downloaded.[/yellow]")
            return

        config = config_manager.get_model_config(model_key)
        if config is None:
            console.print(f"[red]Error: Model '{model_key}' not found[/red]")
            sys.exit(1)

        # Confirm deletion
        if not force:
            confirm = (
                input(
                    f"Delete {config.name}? This will free ~{config.size_gb} GB. (y/n): "
                )
                .strip()
                .lower()
            )
            if confirm != "y":
                console.print("Deletion cancelled.")
                return

        success = model_manager.delete_model(model_key)

        if success:
            console.print(f"[green]✓ {config.name} deleted successfully.[/green]")
        else:
            console.print(f"[red]✗ Failed to delete {config.name}[/red]")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error deleting model: {e}")
        sys.exit(1)


@model_cli.command(name="status")
def model_status() -> None:
    """Show current model configuration status."""
    try:
        from .model_config import get_config_manager
        from .model_manager import get_model_manager

        config_manager = get_config_manager()
        model_manager = get_model_manager()

        console.print("\n[bold cyan]Model Configuration Status[/bold cyan]\n")

        selected = config_manager.get_selected_model()
        if selected:
            key, config = selected
            console.print(f"[bold]Selected Model:[/bold] {config.name} ({key})")
            console.print(f"[bold]Repository:[/bold] {config.repo_id}")

            if config_manager.is_model_downloaded(key):
                info = model_manager.get_model_info(key)
                if info:
                    size_mb = info.get("actual_size_mb", 0)
                    size_gb = size_mb / 1024
                    console.print(
                        f"[bold]Status:[/bold] [green]Downloaded ({size_gb:.2f} GB)[/green]"
                    )
            else:
                console.print(
                    f"[bold]Status:[/bold] [yellow]Not downloaded (~{config.size_gb} GB)[/yellow]"
                )
                console.print(f"\nRun 'identity-gen model download {key}' to download.")
        else:
            console.print("[yellow]No model configured.[/yellow]")
            console.print("\nRun 'identity-gen model configure' to set up a model.")

        # Show cache directory
        console.print(
            f"\n[bold]Cache Directory:[/bold] {config_manager.get_cache_dir()}"
        )

    except Exception as e:
        logger.error(f"Error checking status: {e}")
        sys.exit(1)


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
