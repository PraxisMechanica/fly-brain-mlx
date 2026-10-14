/// <reference path="./native_types_node.d.ts" />
declare module 'node:fs' { export function existsSync(path: string): boolean; }
declare namespace NativePython {
  interface FileSystem extends NativeTypes.NativeFs {
    getOriginalUri(uri: NativeTypes.Uri): NativeTypes.Uri;
    isMappedUri(uri: NativeTypes.Uri): boolean;
  }
  interface Session {
    readonly native: NativeTypes.Loader;
    readonly node_info: unknown;
    bind(path: string): unknown;
    parsed(path: string): NativeTypes.Parsed | undefined;
    diagnostics(path: string): unknown[] | undefined;
  }
  interface Enumeration { matches: Map<string, NativeTypes.Uri>; isComplete: boolean; }
  interface SourceEnumerator { enumerate(milliseconds: number): Enumeration; }
  interface SourceInfo {
    uri: NativeTypes.Uri; isTypeshedFile: boolean; isThirdPartyImport: boolean;
    isThirdPartyPyTypedPresent: boolean; sourceFile: unknown;
  }
  interface Program extends NativeTypes.Program {
    addInterimFile(uri: NativeTypes.Uri): SourceInfo;
    getBoundSourceFile(uri: NativeTypes.Uri): unknown;
    getSourceFileInfoList(): SourceInfo[];
  }
  interface Service extends NativeTypes.RecordValue {
    test_program: Program; _sourceEnumerator: SourceEnumerator;
  }
  interface Environment {
    root: string; python: string; platform: string; extra_paths: string[]; import_roots: string[];
  }
  interface Origin extends NativeTypes.FileInput {
    raw_uri: string; module: string; mapped: boolean; typeshed: boolean; third_party: boolean; py_typed: boolean;
  }
  type Observation = Pick<Report, 'tracked' | 'stub_inputs' | 'stub_path' | 'loaded' | 'environments'>;
  interface ObservationSnapshot extends Observation {
    refreshLoaded(): Origin[];
  }
  interface Report {
    schema: 1; version: string; node_version: string; host_kind: 0; request_sha256: string;
    configuration: NativeTypes.FileInput[]; primary_config: string; diagnostic_rules: [string, string | boolean][];
    include: [string,string][]; exclude: [string,string][]; ignore: [string,string][];
    environments: Environment[]; venv: string | null; venv_path: string | null;
    stub_path: string; configured_typeshed: string | null; tracked: string[]; stub_inputs: string[];
    sources: NativeTypes.FileInput[]; loaded: Origin[]; read_inputs: NativeTypes.FileInput[];
    bridge_sources: NativeTypes.FileInput[]; compiler_artifacts: NativeTypes.FileInput[]; missing: string[];
  }
}
