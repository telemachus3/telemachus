from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Optional

import pandas as pd

from .validate import validate_df_against_arrow_schema


@dataclass(slots=True)
class Frame:
    """
    Lightweight façade around a pandas DataFrame that represents a
    Telemachus-conform table.

    IMPORTANT:
    - No schema is re-declared here. Validation delegates to PyArrow schemas
      defined in telemachus.core.schemas.TABLE_SCHEMAS.
    """
    table: str
    df: pd.DataFrame

    @classmethod
    def from_df(
        cls,
        table: str,
        df: pd.DataFrame,
        *,
        validate: bool = True,
        strict_types: bool = False,
        allow_extra_columns: bool = True,
    ) -> "Frame":
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame")
        if "timestamp" in df.columns:
            # ensure timezone-aware UTC
            df = df.copy()
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
            df = df.sort_values("timestamp").reset_index(drop=True)
        if validate:
            validate_df_against_arrow_schema(
                table, df,
                strict_types=strict_types,
                allow_extra_columns=allow_extra_columns,
            )
        return cls(table=table, df=df)

    @classmethod
    def from_records(
        cls,
        table: str,
        rows: Iterable[Mapping[str, object]],
        *,
        validate: bool = True,
        strict_types: bool = False,
        allow_extra_columns: bool = True,
    ) -> "Frame":
        df = pd.DataFrame.from_records(list(rows))
        return cls.from_df(
            table, df,
            validate=validate,
            strict_types=strict_types,
            allow_extra_columns=allow_extra_columns,
        )

    def to_df(self) -> pd.DataFrame:
        return self.df.copy()

    def head(self, n: int = 5) -> pd.DataFrame:
        return self.df.head(n)

    def select(self, columns: list[str]) -> "Frame":
        return Frame.from_df(self.table, self.df[columns], validate=False)

    def with_column(self, name: str, values) -> "Frame":
        df = self.to_df()
        df[name] = values
        return Frame.from_df(self.table, df, validate=False)

    def validate(
        self,
        *,
        strict_types: bool = False,
        allow_extra_columns: bool = True,
    ) -> None:
        validate_df_against_arrow_schema(
            self.table, self.df,
            strict_types=strict_types,
            allow_extra_columns=allow_extra_columns,
        )