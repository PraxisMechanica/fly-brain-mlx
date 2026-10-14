declare module 'node:crypto' {
  interface Hash { update(value: string | Uint8Array): Hash; digest(encoding: 'hex'): string; }
  export function createHash(algorithm: 'sha256'): Hash;
}
declare module 'node:fs' {
  export function readFileSync(path: string | number): Uint8Array;
  export function readFileSync(path: string | number, encoding: 'utf8'): string;
  export function realpathSync(path: string): string;
}
declare module 'node:module' {
  export function createRequire(path: string): (identifier: string) => unknown;
}
declare module 'node:path' {
  export function join(...parts: string[]): string;
  export function isAbsolute(path: string): boolean;
  export function relative(from: string, to: string): string;
}
declare const process: { versions: {node: string}; stdout: {write(value: string): void}; exitCode?: number; };
declare var __rootDirectory: string;

declare namespace NativeTypes {
  type RecordValue = Record<string, unknown>;
  type ForeignFunction = (...arguments_: unknown[]) => unknown;
  type ForeignConstructor<T> = new (...arguments_: unknown[]) => T;
  interface ModuleValue { exports: unknown; paths?: string[]; children?: unknown[]; }
  interface Loader {
    (id: number): unknown;
    d: (target: RecordValue, getters?: Record<string, () => unknown>, values?: RecordValue) => void;
    o: (value: object, key: PropertyKey) => boolean;
    r: (value: object) => void;
    nmd: (module: ModuleValue) => ModuleValue;
  }
  interface Uri { getFilePath(): string; }
  interface NativeFs {
    readFileSync(uri: Uri, encoding?: string): string | Uint8Array;
  }
  interface Services { dispose(): void; }
  interface Parsed {
    parserOutput: {parseTree: unknown; importedModules: unknown};
    tokenizerOutput: {lines: unknown};
  }
  interface NameNode { nodeType: number; start: number; length: number; }
  interface Position {line: number; character: number;}
  interface Evaluator {
    getTypeOfExpression(node: NameNode): {type: unknown; isIncomplete?: boolean} | undefined;
    inferReturnTypeIfNecessary(type: RecordValue): unknown;
    getDeclInfoForNameNode(node: NameNode): {decls: unknown[]} | undefined;
    resolveAliasDeclaration(declaration: unknown, follow: boolean): unknown;
  }
  interface Program {
    evaluator: Evaluator;
    readonly analyzerNodeInfoReader: unknown;
    setTrackedFiles(uris: Uri[]): unknown;
    analyze(settings: {openFilesTimeInMs: number; noOpenFilesTimeInMs: number}): boolean;
    getParseResults(uri: Uri): Parsed | undefined;
    getParseDiagnostics(uri: Uri): unknown[] | undefined;
    getSourceFileInfoList(): {uri: Uri}[];
    dispose(): void;
  }
  interface Config extends RecordValue { }
  interface TypeHelpers {
    ClassType: {
      isProtocolClass(type: RecordValue): unknown;
      isUnspecialized(type: RecordValue): unknown;
      isHierarchyPartiallyEvaluated(type: RecordValue): unknown;
    };
    FunctionType: {
      isPartiallyEvaluated(type: RecordValue): unknown;
      isGradualCallableForm(type: RecordValue): unknown;
      getParamDefaultType(type: RecordValue, index: number): unknown;
      getParamType(type: RecordValue, index: number): unknown;
      getEffectiveReturnType(type: RecordValue, inferred?: boolean): unknown;
    };
    OverloadedType: {getOverloads(type: RecordValue): unknown; getImplementation(type: RecordValue): unknown;};
    TypeVarKind: {TypeVar: number};
    isPositionOnlySeparator(parameter: RecordValue): unknown;
    isKeywordOnlySeparator(parameter: RecordValue): unknown;
  }
  interface Context {
    program: Program;
    services: Services;
    config: Config;
    Uri: {file(path: string, services: Services): Uri};
    native: Loader;
    readInputs: Map<string, string>;
  }
  interface FileInput {path: string; sha256: string;}
  interface Declaration extends FileInput {
    kind: number; line: number; column: number; end_line: number; end_column: number;
  }
  interface SourceSnapshot {
    declaration(value: unknown): Declaration | null;
  }
  interface Projector {
    context: Context;
    source: SourceSnapshot;
    types: TypeHelpers;
    type(value: unknown): number;
  }
  interface Settings { package: string; extra_paths: string[]; stub_path: string | null; }
}
