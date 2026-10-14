from pathlib import Path

from fly_brain.simulation.identifiers import NeuronRow
from fly_brain.simulation.models import Connectome, InputPin

from . import input_audit_rules as rules
from .ports import (
    AbsoluteCountReader,
    ConnectomeSilencer,
    DestinationBucketsReader,
    DestinationGroupingReader,
    InputAuditFiles,
)


def run(
    connectome: Connectome,
    pin: InputPin,
    output: Path,
    *,
    read_grouping: DestinationGroupingReader,
    read_absolute_counts: AbsoluteCountReader,
    silence: ConnectomeSilencer,
    read_buckets: DestinationBucketsReader,
    files: InputAuditFiles,
) -> dict[str, object]:
    files.create_output(output)
    grouping = read_grouping(connectome)
    rules.validate_grouping(connectome, grouping)
    absolute = read_absolute_counts(connectome)
    rules.validate_absolute_counts(absolute)
    silenced = silence(connectome, (NeuronRow(0),))
    prepared = rules.prepare_archive(connectome, grouping, absolute, silenced)
    artifact = files.write_arrays(output, prepared.arrays)
    header = rules.build_header(connectome, pin, grouping, absolute, prepared)
    identity = files.read_artifact_identity(artifact)
    report = rules.with_artifact(header, identity)
    buckets = read_buckets(connectome)
    report = rules.with_buckets(report, connectome, pin, buckets)
    files.write_report(output, report)
    return report
