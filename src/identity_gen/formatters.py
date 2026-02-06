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

        # Get headers from first item
        headers = list(data[0].keys())

        # Prepare rows
        rows = []
        for item in data:
            row = [str(item.get(h, "")) for h in headers]
            rows.append(row)

        try:
            return tabulate(rows, headers=headers, tablefmt=tablefmt, maxcolwidths=30)
        except TypeError:
            return tabulate(rows, headers=headers, tablefmt=tablefmt)

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

    @staticmethod
    def format_sql(
        identities: List[Identity],
        include_fields: Optional[Set[str]] = None,
        table_name: str = "identities",
    ) -> str:
        """Format identities as SQL INSERT statements.

        Args:
            identities: List of identities to format.
            include_fields: Fields to include.
            table_name: Name of the SQL table.

        Returns:
            SQL INSERT statements.
        """
        if not identities:
            return ""

        data = [identity.to_dict(include_fields) for identity in identities]

        lines = []
        headers = list(data[0].keys())
        columns = ", ".join(headers)

        for item in data:
            values = []
            for h in headers:
                v = item.get(h)
                if v is None:
                    values.append("NULL")
                elif isinstance(v, str):
                    escaped = v.replace("'", "''")
                    values.append(f"'{escaped}'")
                else:
                    values.append(str(v))
            values_str = ", ".join(values)
            lines.append(f"INSERT INTO {table_name} ({columns}) VALUES ({values_str});")

        return "\n".join(lines)

    @staticmethod
    def format_markdown(
        identities: List[Identity],
        include_fields: Optional[Set[str]] = None,
    ) -> str:
        """Format identities as a Markdown table.

        Args:
            identities: List of identities to format.
            include_fields: Fields to include.

        Returns:
            Markdown table string.
        """
        if not identities:
            return ""

        data = [identity.to_dict(include_fields) for identity in identities]

        headers = list(data[0].keys())

        lines = []
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        for item in data:
            row = [str(item.get(h, "")) for h in headers]
            lines.append("| " + " | ".join(row) + " |")

        return "\n".join(lines)

    @staticmethod
    def format_yaml(
        identities: List[Identity],
        include_fields: Optional[Set[str]] = None,
    ) -> str:
        """Format identities as YAML.

        Args:
            identities: List of identities to format.
            include_fields: Fields to include.

        Returns:
            YAML string.
        """
        lines = []
        for i, identity in enumerate(identities, 1):
            lines.append(f"- identity_{i}:")
            data = identity.to_dict(include_fields)
            for key, value in data.items():
                if value is not None:
                    if isinstance(value, str):
                        escaped = str(value).replace('"', '\\"')
                        lines.append(f'    {key}: "{escaped}"')
                    else:
                        lines.append(f"    {key}: {value}")
        return "\n".join(lines)

    @staticmethod
    def format_vcard(
        identities: List[Identity],
        include_fields: Optional[Set[str]] = None,
    ) -> str:
        """Format identities as vCard 3.0 format.

        Args:
            identities: List of identities to format.
            include_fields: Fields to include.

        Returns:
            vCard formatted string.
        """
        vcards = []

        for identity in identities:
            data = identity.to_dict(include_fields)
            lines = ["BEGIN:VCARD", "VERSION:3.0"]

            name_parts = []
            if data.get("last_name"):
                name_parts.append(data["last_name"])
            if data.get("first_name"):
                name_parts.append(data["first_name"])

            if name_parts:
                lines.append(f"N:{';'.join(name_parts)};;;")
                lines.append(f"FN:{''.join(name_parts)}")

            if data.get("email"):
                lines.append(f"EMAIL:{data['email']}")
            if data.get("phone"):
                lines.append(f"TEL:{data['phone']}")
            if data.get("address"):
                addr = str(data["address"]).replace(",", "\\,")
                lines.append(f"ADR:;;{addr};;;;")

            lines.append("END:VCARD")
            vcards.append("\n".join(lines))

        return "\n\n".join(vcards)

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
            OutputFormat.SQL: lambda: cls.format_sql(identities, include_fields),
            OutputFormat.MARKDOWN: lambda: cls.format_markdown(
                identities, include_fields
            ),
            OutputFormat.YAML: lambda: cls.format_yaml(identities, include_fields),
            OutputFormat.VCARD: lambda: cls.format_vcard(identities, include_fields),
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
