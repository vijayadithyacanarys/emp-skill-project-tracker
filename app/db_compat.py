from datetime import date, datetime
import os

from sqlalchemy import Boolean, Date, DateTime, String, Text, column, literal
from sqlalchemy.dialects import mssql
from sqlalchemy.engine import make_url
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.functions import FunctionElement
from sqlalchemy.sql.type_api import TypeEngine


MSSQL_TEXT_COLLATION = "Latin1_General_100_CS_AS_SC"
MSSQL_BINARY_COLLATION = "Latin1_General_100_BIN2"


def is_mssql_database_configured() -> bool:
    database_url = os.environ.get("DATABASE_URL")
    return (
        database_url is not None
        and make_url(database_url).get_backend_name() == "mssql"
    )


def validate_email_whitespace(value: object, dialect_name: str) -> None:
    if (
        dialect_name == "mssql"
        and isinstance(value, str)
        and value != value.strip()
    ):
        raise ValueError("Email must not contain leading or trailing whitespace")


class _ExactStringIn(FunctionElement[bool]):
    type = Boolean()
    inherit_cache = True


class _ExactStringEqual(FunctionElement[bool]):
    type = Boolean()
    inherit_cache = True


class _CurrentTimestamp(FunctionElement[datetime]):
    type = DateTime(timezone=True)
    inherit_cache = True


@compiles(_ExactStringEqual)
def _compile_exact_string_equal(element, compiler, **kwargs):
    column_sql, value_sql = (
        compiler.process(clause, **kwargs)
        for clause in element.clauses
    )
    return f"{column_sql} = {value_sql}"


@compiles(_ExactStringEqual, "mssql")
def _compile_exact_string_equal_mssql(element, compiler, **kwargs):
    column_sql, value_sql = (
        compiler.process(clause, **kwargs)
        for clause in element.clauses
    )
    return (
        f"(({column_sql} COLLATE {MSSQL_BINARY_COLLATION}) = {value_sql} "
        f"AND DATALENGTH({column_sql}) = DATALENGTH({value_sql}))"
    )


@compiles(_ExactStringIn)
def _compile_exact_string_in(element, compiler, **kwargs):
    clauses = list(element.clauses)
    column_sql = compiler.process(clauses[0], **kwargs)
    values_sql = ", ".join(
        compiler.process(clause, literal_binds=True)
        for clause in clauses[1:]
    )
    return f"{column_sql} IN ({values_sql})"


@compiles(_ExactStringIn, "mssql")
def _compile_exact_string_in_mssql(element, compiler, **kwargs):
    clauses = list(element.clauses)
    column_sql = compiler.process(clauses[0], **kwargs)
    values_sql = ", ".join(
        f"N{compiler.process(clause, literal_binds=True)}"
        for clause in clauses[1:]
    )
    return (
        f"(({column_sql} COLLATE Latin1_General_100_BIN2) IN ({values_sql}) "
        f"AND DATALENGTH({column_sql}) = "
        f"DATALENGTH(RTRIM({column_sql})))"
    )


@compiles(_CurrentTimestamp)
def _compile_current_timestamp(_element, _compiler, **_kwargs):
    return "CURRENT_TIMESTAMP"


@compiles(_CurrentTimestamp, "mssql")
def _compile_current_timestamp_mssql(_element, _compiler, **_kwargs):
    return "SYSDATETIMEOFFSET()"


def exact_string_equal(
    expression: ColumnElement[str],
    value: str,
) -> FunctionElement[bool]:
    return _ExactStringEqual(
        expression,
        literal(value, type_=expression.type),
    )


def current_timestamp_expression() -> FunctionElement[datetime]:
    return _CurrentTimestamp()


def exact_string_in(column_name: str, values: tuple[str, ...]) -> FunctionElement[bool]:
    return _ExactStringIn(
        column(column_name),
        *(literal(value, type_=String()) for value in values),
    )


def unicode_string(length: int) -> TypeEngine[str]:
    return String(length).with_variant(
        mssql.NVARCHAR(length, collation=MSSQL_TEXT_COLLATION),
        "mssql",
    )


def unicode_text() -> TypeEngine[str]:
    return Text().with_variant(
        mssql.NVARCHAR(None, collation=MSSQL_TEXT_COLLATION),
        "mssql",
    )


def ascii_string(length: int) -> TypeEngine[str]:
    return String(length).with_variant(
        mssql.VARCHAR(length, collation=MSSQL_TEXT_COLLATION),
        "mssql",
    )


def date_type() -> TypeEngine[date]:
    return Date().with_variant(mssql.DATE(), "mssql")
