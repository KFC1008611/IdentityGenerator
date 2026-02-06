"""Extra edge-case tests for formatter uncovered branches."""

from identity_gen.formatters import IdentityFormatter
from identity_gen.models import Identity
from typing import Any, cast


def test_format_sql_null_value_branch() -> None:
    identities: Any = [
        type("X", (), {"to_dict": lambda self, _=None: {"name": None}})()
    ]
    out = IdentityFormatter.format_sql(identities)
    assert "NULL" in out


def test_write_output_stdout_branch(capsys) -> None:
    IdentityFormatter.write_output("hello", output_path=None)
    captured = capsys.readouterr()
    assert "hello" in captured.out


def test_format_unknown_raises() -> None:
    identity = Identity.model_validate({"name": "张三"})
    unknown = cast(Any, "unknown")
    try:
        IdentityFormatter.format([identity], unknown)
    except ValueError as exc:
        assert "Unknown format" in str(exc)
