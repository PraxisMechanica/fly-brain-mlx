from tools.architecture.native_calls_records import NativeCallReport


def validate_call_report(report: NativeCallReport) -> None:
    typing = report.typing
    sources = report.sources
    calls = report.calls
    if not sources or not calls or len({call.node_id for call in calls}) != len(calls):
        raise ValueError(
            'COV002: native explicit call discovery is empty or duplicated'
        )
    expected = tuple(
        (call.location.path, call.location.line, call.location.column, index)
        for call in calls
        for index in (
            call.callee_type,
            call.receiver_type,
            call.selected_signature,
            call.result_type,
            *(arg.type for arg in call.arguments),
        )
        if index is not None
    )
    observed = tuple(
        (site.path, site.line, site.column, site.type) for site in typing.sites
    )
    if observed != expected:
        raise ValueError('COV002: native call type-site coverage differs')
    for source in sources:
        for call in source.calls:
            if call.location.path != source.path or call.sha256 != source.sha256:
                raise ValueError('COV002: native call location/source identity differs')
            signature = report.signature(call)
            if signature.category != 'function' or signature.declaration is None:
                raise ValueError(
                    f'COV002: native callable declaration is erased at {call.location.path}:{call.location.line}:{call.location.column}'
                )
            callee = typing.types[call.callee_type]
            if call.overload_index is not None:
                if callee.category != 'overloaded' or call.overload_index >= len(
                    callee.overloads
                ):
                    raise ValueError(
                        'COV002: native selected overload identity is absent'
                    )
                selected = typing.types[callee.overloads[call.overload_index]]
                if selected.declaration != signature.declaration:
                    raise ValueError(
                        'COV002: native selected overload declaration differs'
                    )
            elif callee.category == 'overloaded':
                raise ValueError('COV002: native selected overload index is missing')
            if call.protocol != (
                call.receiver_type is not None
                and typing.types[call.receiver_type].protocol is True
            ):
                raise ValueError(
                    'COV002: native declared Protocol receiver identity differs'
                )
    for site in typing.sites:
        typing.require_precise(site)
