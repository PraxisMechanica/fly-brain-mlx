import io
import token
import tokenize
import unicodedata
from bisect import bisect_left
from pathlib import Path

from tools.architecture.symbols import Location


class Coordinates:
    def __init__(self, path: Path, text: str) -> None:
        self.path = str(path.resolve())
        self.lines = text.splitlines(keepends=True) or ['']
        self.tokens = tuple(tokenize.generate_tokens(io.StringIO(text).readline))
        self.names = tuple(item for item in self.tokens if item.type == token.NAME)
        self.name_starts = tuple(item.start for item in self.names)

    def utf16_column(self, line: int, column: int) -> int:
        if line < 1 or line > len(self.lines):
            raise ValueError('COV002: source line is outside the document')
        text = self.lines[line - 1]
        if column < 0 or column > len(text):
            raise ValueError('COV002: source column is outside the document')
        return len(text[:column].encode('utf-16-le')) // 2

    def ast_column(self, line: int, byte_column: int) -> int:
        if line < 1 or line > len(self.lines) or byte_column < 0:
            raise ValueError('COV002: AST position is outside the document')
        encoded = self.lines[line - 1].encode('utf-8')
        if byte_column > len(encoded):
            raise ValueError('COV002: AST byte column is outside the document')
        try:
            return len(encoded[:byte_column].decode('utf-8'))
        except UnicodeError as error:
            raise ValueError('COV002: AST position splits a UTF-8 character') from error

    def location(self, start: tuple[int, int], end: tuple[int, int]) -> Location:
        return Location(
            self.path,
            start[0],
            self.utf16_column(*start),
            end[0],
            self.utf16_column(*end),
        )

    def ast_bounds(
        self, line: int, column: int, end_line: int, end_column: int
    ) -> tuple[tuple[int, int], tuple[int, int]]:
        return (
            (line, self.ast_column(line, column)),
            (end_line, self.ast_column(end_line, end_column)),
        )

    def identifier(
        self,
        line: int,
        column: int,
        end_line: int,
        end_column: int,
        *,
        last: bool = False,
        declaration: bool = False,
    ) -> Location:
        start, end = self.ast_bounds(line, column, end_line, end_column)
        candidates = self.names_in(start, end)
        if declaration:
            for index, item in enumerate(candidates):
                if item.string in ('class', 'def') and index + 1 < len(candidates):
                    chosen = candidates[index + 1]
                    return self.location(chosen.start, chosen.end)
        elif candidates:
            chosen = candidates[-1] if last else candidates[0]
            return self.location(chosen.start, chosen.end)
        raise ValueError('COV002: source identifier has no exact token location')

    def names_in(
        self, start: tuple[int, int], end: tuple[int, int]
    ) -> tuple[tokenize.TokenInfo, ...]:
        return tuple(
            item
            for item in self.names[
                bisect_left(self.name_starts, start) : bisect_left(
                    self.name_starts, end
                )
            ]
            if item.end <= end
        )

    def attribute(self, end_line: int, end_column: int, name: str) -> Location:
        end = self.ast_column(end_line, end_column)
        text = self.lines[end_line - 1]
        start = end
        while start > 0 and ('a' + text[start - 1]).isidentifier():
            start -= 1
        spelling = text[start:end]
        if (
            not spelling.isidentifier()
            or unicodedata.normalize('NFKC', spelling) != name
        ):
            raise ValueError('COV002: attribute has no exact source identifier span')
        return self.location((end_line, start), (end_line, end))
