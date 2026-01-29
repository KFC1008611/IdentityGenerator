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
        OutputFormat.TABLE: "csv",
        OutputFormat.RAW: "txt",
        OutputFormat.SQL: "sql",
        OutputFormat.MARKDOWN: "md",
        OutputFormat.YAML: "yaml",
        OutputFormat.VCARD: "vcf",
    }
    ext = extensions.get(output_format, "csv")
    return f"identities_{timestamp}.{ext}"


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


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
