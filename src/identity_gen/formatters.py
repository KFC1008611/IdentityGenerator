"""Output format handlers for identity data."""

import csv
import json
import sys
from io import StringIO
from typing import List, Optional, Set, TextIO

from tabulate import tabulate

from .models import Identity, OutputFormat


class IdentityFormatter:
    """Formatter for identity output."""

    @staticmethod
    def format_json(
        identities: List[Identity],
        include_fields: Optional[Set[str]] = None,
        indent: int = 2,
    ) -> str:
        """Format identities as JSON.

        Args:
            identities: List of identities to format.
            include_fields: Fields to include.
            indent: JSON indentation level.

        Returns:
            JSON string.
        """
        data = [identity.to_dict(include_fields) for identity in identities]
        return json.dumps(data, indent=indent, default=str, ensure_ascii=False)

    @staticmethod
    def format_csv(
        identities: List[Identity],
        include_fields: Optional[Set[str]] = None,
    ) -> str:
        """Format identities as CSV.

        Args:
            identities: List of identities to format.
            include_fields: Fields to include.

        Returns:
            CSV string.
        """
        if not identities:
            return ""

        output = StringIO()

        # Determine fields from first identity
        first_dict = identities[0].to_dict(include_fields)
        fieldnames = list(first_dict.keys())

        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for identity in identities:
            row = identity.to_dict(include_fields)
            # Convert non-string values
            for key, value in row.items():
                if value is not None and not isinstance(value, str):
                    row[key] = str(value)
            writer.writerow(row)

        return output.getvalue()

    @staticmethod
    def format_table(
        identities: List[Identity],
        include_fields: Optional[Set[str]] = None,
        tablefmt: str = "grid",
    ) -> str:
        """Format identities as a table.

        Args:
            identities: List of identities to format.
            include_fields: Fields to include.
            tablefmt: Table format (grid, simple, pipe, etc.).

        Returns:
            Formatted table string.
        """
        if not identities:
            return "No identities to display."

        data = [identity.to_dict(include_fields) for identity in identities]

        if not data:
            return "No data to display."

        # Get headers from first item
        headers = list(data[0].keys())

        # Prepare rows
        rows = []
        for item in data:
            row = [str(item.get(h, "")) for h in headers]
            rows.append(row)

        return tabulate(rows, headers=headers, tablefmt=tablefmt, maxcolwidths=30)

    @staticmethod
    def format_raw(identities: List[Identity]) -> str:
        """Format identities in simple text format.

        Args:
            identities: List of identities to format.

        Returns:
            Simple text representation.
        """
        lines = []
        for i, identity in enumerate(identities, 1):
            lines.append(f"Identity #{i}")
            lines.append("-" * 40)
            data = identity.to_dict()
            for key, value in data.items():
                if value is not None:
                    lines.append(f"  {key}: {value}")
            lines.append("")
        return "\n".join(lines)

    @classmethod
    def format(
        cls,
        identities: List[Identity],
        output_format: OutputFormat,
        include_fields: Optional[Set[str]] = None,
    ) -> str:
        """Format identities according to specified format.

        Args:
            identities: List of identities to format.
            output_format: Desired output format.
            include_fields: Fields to include.

        Returns:
            Formatted string.
        """
        formatters = {
            OutputFormat.JSON: lambda: cls.format_json(identities, include_fields),
            OutputFormat.CSV: lambda: cls.format_csv(identities, include_fields),
            OutputFormat.TABLE: lambda: cls.format_table(identities, include_fields),
            OutputFormat.RAW: lambda: cls.format_raw(identities),
        }

        formatter = formatters.get(output_format)
        if not formatter:
            raise ValueError(f"Unknown format: {output_format}")

        return formatter()

    @staticmethod
    def write_output(
        content: str,
        output_path: Optional[str] = None,
        encoding: str = "utf-8",
    ) -> None:
        """Write formatted content to file or stdout.

        Args:
            content: Content to write.
            output_path: Path to output file. If None, writes to stdout.
            encoding: File encoding.
        """
        if output_path:
            with open(output_path, "w", encoding=encoding) as f:
                f.write(content)
        else:
            print(content)
