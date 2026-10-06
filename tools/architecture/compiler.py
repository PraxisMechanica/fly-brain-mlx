import json
import os
import select
import subprocess
from pathlib import Path
from time import monotonic
from types import TracebackType
from typing import TypeAlias, cast

JsonValue: TypeAlias = (
    str | int | float | bool | None | list['JsonValue'] | dict[str, 'JsonValue']
)


def object_value(value: JsonValue) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise ValueError('COV002: compiler response is not an object')
    return value


def content_length(header: bytes) -> int:
    try:
        fields: dict[str, str] = {}
        for line in header.decode('ascii').split('\r\n'):
            key, value = line.split(':', 1)
            key = key.strip().lower()
            if key in fields:
                raise ValueError('duplicate header')
            fields[key] = value.strip()
        length = int(fields['content-length'])
        if length <= 0:
            raise ValueError('empty response')
    except (UnicodeError, ValueError, KeyError) as error:
        raise ValueError('COV002: compiler response framing is invalid') from error
    return length


class Compiler:
    def __init__(self, root: Path, executable: Path) -> None:
        self.root = root.resolve()
        self.executable = executable
        self.sequence = 0
        self.process: subprocess.Popen[bytes] | None = None
        self.opened: dict[Path, str] = {}
        self.buffer = bytearray()
        self.capabilities: dict[str, JsonValue] = {}

    def __enter__(self) -> 'Compiler':
        if self.process is not None:
            raise ValueError('COV002: compiler transport is already open')
        if not self.executable.is_file():
            raise ValueError('COV002: native compiler language server is missing')
        try:
            self.process = subprocess.Popen(
                [str(self.executable), '--stdio'],
                cwd=self.root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                bufsize=0,
            )
        except OSError as error:
            raise ValueError('COV002: native compiler could not start') from error
        try:
            result = object_value(
                self.request(
                    'initialize',
                    {
                        'processId': None,
                        'rootUri': self.root.as_uri(),
                        'capabilities': {
                            'workspace': {'configuration': True},
                            'textDocument': {
                                'declaration': {'dynamicRegistration': True}
                            },
                        },
                        'workspaceFolders': [
                            {'uri': self.root.as_uri(), 'name': 'architecture'}
                        ],
                    },
                )
            )
            capabilities = object_value(result.get('capabilities'))
            self.capabilities = capabilities
            for required in (
                'definitionProvider',
                'typeDefinitionProvider',
                'hoverProvider',
            ):
                if not capabilities.get(required):
                    raise ValueError('COV002: compiler lacks ' + required)
            self.notify('initialized', {})
        except BaseException:
            self.close()
            raise
        return self

    def send(self, message: dict[str, JsonValue]) -> None:
        if self.process is None or self.process.stdin is None:
            raise ValueError('COV002: compiler transport is not open')
        payload = json.dumps(message, allow_nan=False).encode()
        frame = f'Content-Length: {len(payload)}\r\n\r\n'.encode() + payload
        try:
            remaining = memoryview(frame)
            while remaining:
                written = self.process.stdin.write(remaining)
                if not written:
                    raise ValueError('COV002: compiler request write is incomplete')
                remaining = remaining[written:]
            self.process.stdin.flush()
        except OSError as error:
            raise ValueError('COV002: compiler transport write failed') from error

    def read(self, deadline: float) -> None:
        if self.process is None or self.process.stdout is None:
            raise ValueError('COV002: compiler transport is not open')
        output = self.process.stdout
        remaining = deadline - monotonic()
        if remaining <= 0 or not select.select([output], [], [], remaining)[0]:
            raise ValueError('COV002: compiler response timed out')
        chunk = os.read(output.fileno(), 65536)
        if not chunk:
            raise ValueError('COV002: compiler response ended before completion')
        self.buffer.extend(chunk)

    def receive(self, deadline: float | None = None) -> dict[str, JsonValue]:
        if deadline is None:
            deadline = monotonic() + 30
        while (end := self.buffer.find(b'\r\n\r\n')) < 0:
            self.read(deadline)
        length = content_length(bytes(self.buffer[:end]))
        start = end + 4
        while len(self.buffer) < start + length:
            self.read(deadline)
        payload = bytes(self.buffer[start : start + length])
        del self.buffer[: start + length]
        try:
            value = cast(JsonValue, json.loads(payload))
        except (ValueError, UnicodeError) as error:
            raise ValueError('COV002: compiler response JSON is invalid') from error
        return object_value(value)

    def request(self, method: str, parameters: JsonValue) -> JsonValue:
        self.sequence += 1
        identifier = self.sequence
        self.send(
            {'jsonrpc': '2.0', 'id': identifier, 'method': method, 'params': parameters}
        )
        deadline = monotonic() + 30
        while True:
            if monotonic() >= deadline:
                raise ValueError('COV002: compiler response timed out')
            response = self.receive(deadline)
            if response.get('method') and 'id' in response:
                if response['method'] != 'workspace/configuration':
                    raise ValueError(
                        'COV002: unsupported compiler request: '
                        + str(response['method'])
                    )
                items = object_value(response.get('params')).get('items')
                if not isinstance(items, list):
                    raise ValueError('COV002: invalid compiler configuration request')
                self.send(
                    {
                        'jsonrpc': '2.0',
                        'id': response['id'],
                        'result': [{} for _ in items],
                    }
                )
            elif 'id' in response:
                if response['id'] != identifier:
                    raise ValueError('COV002: unexpected compiler response identity')
                if 'error' in response:
                    raise ValueError(
                        'COV002: compiler error: ' + json.dumps(response['error'])
                    )
                if 'result' not in response:
                    raise ValueError('COV002: compiler result is missing')
                return response['result']

    def notify(self, method: str, parameters: JsonValue) -> None:
        self.send({'jsonrpc': '2.0', 'method': method, 'params': parameters})

    def resolve(self, path: Path, line: int, column: int) -> dict[str, JsonValue]:
        path = path.resolve()
        try:
            content = path.read_text()
        except (OSError, UnicodeError) as error:
            raise ValueError('COV002: compiler source could not be read') from error
        if path in self.opened and self.opened[path] != content:
            raise ValueError('COV002: source changed during compiler analysis')
        if path not in self.opened:
            self.notify(
                'textDocument/didOpen',
                {
                    'textDocument': {
                        'uri': path.as_uri(),
                        'languageId': 'python',
                        'version': 1,
                        'text': content,
                    }
                },
            )
            self.opened[path] = content
        parameters: JsonValue = {
            'textDocument': {'uri': path.as_uri()},
            'position': {'line': line - 1, 'character': column},
        }
        result = {
            name: self.request('textDocument/' + method, parameters)
            for name, method in (
                ('definitions', 'definition'),
                ('types', 'typeDefinition'),
                ('signature', 'hover'),
            )
        }
        if not result['definitions'] or not result['signature']:
            raise ValueError(
                f'COV002: unresolved source symbol: {path}:{line}:{column}'
            )
        return result

    def close(self) -> None:
        process = self.process
        if process is not None:
            try:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=10)
            finally:
                for pipe in (process.stdin, process.stdout, process.stderr):
                    if pipe is not None:
                        pipe.close()
                self.process = None
        self.opened.clear()
        self.buffer.clear()
        self.capabilities.clear()

    def __exit__(
        self,
        error_type: type[BaseException] | None,
        error: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
