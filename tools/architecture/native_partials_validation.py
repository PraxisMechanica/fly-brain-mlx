from tools.architecture.native_partials_records import PartialConstructionReport
from tools.architecture.native_types import NativeDeclaration

PARTIAL_STUB_SHA256 = '09683310003974eee453bf8851422cd8e8a6f6226db465bbccc30f39da446140'


def validate_partial_report(report: PartialConstructionReport) -> None:
    typing = report.typing
    constructions = report.constructions
    if not constructions or len({value.node_id for value in constructions}) != len(
        constructions
    ):
        raise ValueError('COV002: native partial discovery is empty or duplicated')
    expected = tuple(
        (value.location.path, value.location.line, value.location.column, index)
        for value in constructions
        for index in (
            value.callee_type,
            value.constructor_signature,
            value.wrapped.type,
            *(capture.expression.type for capture in value.captures),
            value.result_type,
            value.residual_signature,
        )
    )
    if (
        tuple((site.path, site.line, site.column, site.type) for site in typing.sites)
        != expected
    ):
        raise ValueError('COV002: native partial type-site coverage differs')
    inputs = dict(typing.inputs)
    declarations: list[NativeDeclaration] = [
        value.declaration for value in typing.types if value.declaration is not None
    ]
    for source in report.sources:
        for value in source.constructions:
            if (value.location.path, value.sha256) != (source.path, source.sha256):
                raise ValueError(
                    'COV002: native partial location/source identity differs'
                )
            if any(
                (
                    value.is_incomplete,
                    value.type_errors,
                    value.callee_is_incomplete,
                    value.callee_type_errors,
                )
            ):
                raise ValueError(
                    'COV002: native partial result is incomplete or erroneous'
                )
            for expression in (
                value.wrapped,
                *(capture.expression for capture in value.captures),
            ):
                if any((expression.is_incomplete, expression.type_errors)):
                    raise ValueError(
                        'COV002: native partial expression is incomplete or erroneous'
                    )
                at = expression.location
                if (
                    at.path != source.path
                    or (at.line, at.column)
                    < (value.location.line, value.location.column)
                    or (at.end_line, at.end_column)
                    > (value.location.end_line, value.location.end_column)
                ):
                    raise ValueError(
                        'COV002: native partial expression escapes its construction'
                    )
                declarations.extend(expression.declarations)
            names = (
                'functools.partial',
                'functools.partial.__new__',
                'functools.partial',
                'functools.partial.__call__',
            )
            categories = ('class', 'function', 'class', 'function')
            positions = ((171, 6), (178, 8), (171, 6), (179, 8))
            library_paths: set[str] = set()
            for index, name, category, position in zip(
                (
                    value.callee_type,
                    value.constructor_signature,
                    value.result_type,
                    value.residual_signature,
                ),
                names,
                categories,
                positions,
                strict=True,
            ):
                native = typing.types[index]
                declaration = native.declaration
                if declaration is None or (
                    native.name,
                    native.category,
                    declaration.sha256,
                    (declaration.location.line, declaration.location.column),
                ) != (name, category, PARTIAL_STUB_SHA256, position):
                    raise ValueError('COV002: native partial library identity differs')
                library_paths.add(declaration.location.path)
            if len(library_paths) != 1:
                raise ValueError('COV002: native partial library source differs')
    if any(inputs.get(value.location.path) != value.sha256 for value in declarations):
        raise ValueError('COV002: native partial declaration input identity differs')
