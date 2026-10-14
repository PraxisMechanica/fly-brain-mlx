/// <reference path="./native_python_context_api.d.ts" />
declare namespace NativeBoundDeclarations {
  interface Node extends NativeTypes.RecordValue {
    id: number; nodeType: number; start: number; length: number; d: NativeTypes.RecordValue;
  }
  interface Position { readonly line: number; readonly character: number; }
  interface Range { readonly start: Position; readonly end: Position; }
  interface ParsedNode {
    readonly native_id: number; readonly native_kind: number;
    readonly start: number; readonly length: number; readonly lexical_uri: string;
    readonly span: Range; readonly name: string | null; readonly unreachable: boolean;
  }
  interface Scope extends NativeTypes.RecordValue {
    symbolTable: Map<unknown, unknown>; notLocalBindings: Map<unknown, unknown>;
  }
  interface ObservedScope {
    readonly index: number; readonly native_kind: number; readonly owner: number;
    readonly parent: number | null; readonly parent_kind: number | null;
    readonly dynamic: boolean; readonly nonlocal_bindings: readonly (readonly [string, number])[];
  }
  interface Binding {
    readonly scope: number; readonly name: string; readonly native_symbol_id: number;
    readonly native_flags: number; readonly declarations: readonly number[];
  }
  interface Declaration {
    readonly index: number; readonly native_category: number; readonly node: ParsedNode;
    readonly origin: 'intrinsic' | 'parsed' | 'unmatched_native_node';
    readonly raw_uri: string; readonly raw_range: Range; readonly fallback_uri: string | null;
  }
  interface Observation {
    readonly path: string; readonly capability: 'native_bound_declarations';
    readonly missing: readonly string[]; readonly nodes: readonly ParsedNode[];
    readonly scopes: readonly ObservedScope[]; readonly bindings: readonly Binding[];
    readonly declarations: readonly Declaration[];
  }
}
