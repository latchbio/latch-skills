from dataclasses import dataclass, field, asdict
from pathlib import Path
from types import NoneType
from typing import Dict, Any, List, Sequence, Final
from lib.common_const import SOURCE_ID, LIBRARY_TYPE, MODALITY
from collections import defaultdict
import yaml
import __main__

import polars as pl

# Constants
PROCESS_NAME: Final[str] = "process_name"
METRICS: Final[str] = "metrics"
METRIC_KEY: Final[str] = "metric_key"
VALUE: Final[str] = "value"


@dataclass
class MetricRecord:
    """A single metrics document for one sample/library_type/process."""

    source_id: str
    library_type: str
    modality: str
    process_name: str | None = None
    metrics: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.process_name is None:
            self.process_name = Path(__main__.__file__).name.rstrip(".py")

    def set(self, key: str, value: Any) -> None:
        """Set/overwrite a metric."""
        self.metrics[key] = value

    def update(self, data: Dict[str, Any]) -> None:
        """Bulk update metrics."""
        self.metrics.update(data)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize record to a plain dict suitable for YAML."""
        d = asdict(self)
        return d

    def to_yaml(self) -> str:
        """Return YAML string."""
        return yaml.safe_dump(self.to_dict(), sort_keys=False)

    def write_yaml(self, path: Path | str) -> None:
        """Write YAML to disk."""
        path = Path(path)
        with path.open("w") as f:
            yaml.safe_dump(self.to_dict(), f, sort_keys=False)


@dataclass
class MetricsCollector:
    """Collects MetricRecord objects for a run and writes/aggregates them."""

    records: List[MetricRecord] = field(default_factory=list)
    aggregated: Dict[str, Dict[str, Dict[str, Dict[str, Any]]]] | None = None
    df: pl.DataFrame | None = None

    def generate_df(self) -> None:
        """Generate a Polars DataFrame from the collected metrics. Currently limited to ints and floats"""
        rows: List[Dict[str, Any]] = []

        for rec in self.records:
            for metric_key, value in rec.metrics.items():
                row = {
                    SOURCE_ID: rec.source_id,
                    LIBRARY_TYPE: rec.library_type,
                    MODALITY: rec.modality,
                }
                temp = {}
                if not isinstance(value, (int, float, NoneType)):
                    print(f"{metric_key} value is not int or float, skipping...")
                    continue
                temp[METRIC_KEY] = metric_key
                temp[VALUE] = value
                row.update(temp)
                rows.append(row)
        schema = {
            SOURCE_ID: pl.Enum(list({r[SOURCE_ID] for r in rows})),
            LIBRARY_TYPE: pl.Enum(list({r[LIBRARY_TYPE] for r in rows})),
            MODALITY: pl.Enum(list({r[MODALITY] for r in rows})),
            METRIC_KEY: pl.Enum(list({r[METRIC_KEY] for r in rows})),
            VALUE: pl.Float64,
        }

        self.df = pl.DataFrame(rows, schema=schema)

    def add(self, record: MetricRecord) -> None:
        self.records.append(record)

    def write_all(
        self,
        out_dir: Path,
        filename_fmt: str = "{source_id}.{library_type}.{modality}.yaml",
    ) -> List[Path]:
        """Write each record to out_dir/filename_fmt."""
        written: List[Path] = []
        for rec in self.records:
            fname = filename_fmt.format(
                source_id=rec.source_id,
                library_type=rec.library_type,
                modality=rec.modality,
            )
            path = out_dir / fname
            rec.write_yaml(path)
            written.append(path)
        return written

    def write_aggregated(self, out_dir: Path, source_id: str, output_type: str) -> None:
        if self.aggregated is not None:
            if source_id not in self.aggregated:
                raise ValueError(f"No aggregated data for source_id '{source_id}'")
            if output_type == "yaml":
                path = out_dir / "metrics.yaml"
                with open(path, "w") as out_yaml:
                    yaml.safe_dump(self.aggregated, out_yaml)
            elif output_type == "csv":
                path = out_dir / "metrics.csv"
                if self.df is None:
                    self.generate_df()
                if self.df is not None:
                    self.df.write_csv(path, null_value="NA")
            else:
                print("Unsupported output type")
        else:
            print("Nothing has been aggregated")

    @staticmethod
    def load_metrics(path: Path) -> MetricRecord:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return MetricRecord(
            source_id=data[SOURCE_ID],
            library_type=data[LIBRARY_TYPE],
            process_name=data[PROCESS_NAME],
            modality=data[MODALITY],
            metrics=data.get(METRICS, {}),
        )

    def scan_dir(self, root: Path) -> None:
        """Load all *.yaml below root."""
        recs: List[MetricRecord] = []
        for p in root.rglob("*metrics.yaml"):
            if p.is_file():
                recs.append(MetricsCollector.load_metrics(p))
        self.records = recs

    def aggregate(
        self,
        key_order: Sequence[str] = (SOURCE_ID, LIBRARY_TYPE, MODALITY),
    ) -> None:
        """
        Build `self.aggregated` as a nested dict whose levels
        are controlled by `key_order`.

        Any record missing a requested key is silently skipped.
        """
        # sanity check – only known keys allowed
        allowed = {SOURCE_ID, LIBRARY_TYPE, MODALITY}
        bad = [k for k in key_order if k not in allowed]
        if bad:
            raise ValueError(f"Unknown key(s) in key_order: {bad}")

        # recursive tree that auto-vivifies dicts
        def tree():
            return defaultdict(tree)

        root = tree()

        # build the hierarchy
        for rec in self.records:
            node = root
            for k in key_order:
                val = getattr(rec, k, None)
                if val is None:  # skip the whole record
                    break
                node = node[val]
            else:  # only runs if *all* keys were present
                node.update(rec.metrics)

        # convert defaultdict → plain dict for YAML / JSON friendliness
        def freeze(d):
            if isinstance(d, defaultdict):
                return {k: freeze(v) for k, v in d.items()}
            return d

        self.aggregated = freeze(root)
