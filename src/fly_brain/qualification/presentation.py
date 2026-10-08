from collections.abc import Iterator, Mapping
from itertools import islice
from pathlib import Path
from typing import cast


def _text(value: str) -> str:
    if len(value) <= 200:
        return value
    return value[:160] + f' [{len(value) - 160} characters omitted]'


def _scalar(value: object) -> object:
    if isinstance(value, str):
        return _text(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, (Mapping, list, tuple)):
        items = cast(Mapping[object, object] | list[object] | tuple[object, ...], value)
        return {'type': type(items).__name__, 'items': len(items)}
    return {'type': type(value).__name__}


def _preview(value: object) -> object:
    if isinstance(value, Mapping):
        items = cast(Mapping[object, object], value)
        return {
            'items': [
                {'field': _text(str(key)), 'value': _scalar(item)}
                for key, item in islice(items.items(), 5)
            ],
            'omitted_items': max(0, len(items) - 5),
        }
    if isinstance(value, (list, tuple)):
        items = cast(list[object] | tuple[object, ...], value)
        return {
            'items': [_scalar(item) for item in items[:5]],
            'omitted_items': max(0, len(items) - 5),
        }
    return _scalar(value)


def _fields(value: object, path: str = '') -> Iterator[tuple[str, str, object]]:
    if isinstance(value, Mapping):
        for key, item in cast(Mapping[object, object], value).items():
            name = str(key)
            location = f'{path}.{name}' if path else name
            yield location, name, item
            yield from _fields(item, location)
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(cast(list[object] | tuple[object, ...], value)):
            location = f'{path}[{index}]'
            yield location, str(index), item
            yield from _fields(item, location)


def diagnostic_display(
    report: dict[str, object], output: Path, exit_code: int
) -> dict[str, object]:
    priority = (
        'accepted',
        'case_accepted',
        'full_matrix_accepted',
        'scientific_review_required',
        'diagnostic_assertions_passed',
        'scalar_qualification_passed',
        'tests',
        'failures',
        'errors',
        'skipped',
        'cases',
        'steps',
        'trials',
        'scope',
        'reason',
    )
    selected = {key: report[key] for key in priority if key in report}
    selected.update(
        (key, value)
        for key, value in report.items()
        if key not in selected
        and (value is None or isinstance(value, (str, bool, int, float)))
    )
    summary = {
        _text(key): _preview(value) for key, value in islice(selected.items(), 20)
    }
    false_examples: list[str] = []
    alert_examples: list[dict[str, object]] = []
    false_total = alert_total = 0
    for path, name, value in _fields(report):
        if value is False:
            false_total += 1
            if len(false_examples) < 10:
                false_examples.append(_text(path))
        if name in (
            'failures',
            'errors',
            'skipped',
            'first_divergence',
            'first_budget_violation',
            'first_spike_step',
            'first_different_spike',
        ) and (value is not None if name.startswith('first_') else bool(value)):
            alert_total += 1
            if len(alert_examples) < 10:
                alert_examples.append({'field': _text(path), 'value': _preview(value)})
    return {
        'kind': 'diagnostic',
        'output': _text(str(output)),
        'exit_code': exit_code,
        'summary': summary,
        'omitted_fields': len(report) - len(summary),
        'false_flags': {
            'total': false_total,
            'examples': false_examples,
            'omitted': false_total - len(false_examples),
        },
        'alerts': {
            'total': alert_total,
            'examples': alert_examples,
            'omitted': alert_total - len(alert_examples),
        },
    }
