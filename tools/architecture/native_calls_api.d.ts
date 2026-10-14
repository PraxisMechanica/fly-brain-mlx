/// <reference path="./native_types_node.d.ts" />

declare namespace NativeCalls {
  interface Node extends NativeTypes.NameNode, NativeTypes.RecordValue {
    id: number;
    d: NativeTypes.RecordValue;
  }
  interface TypeResult {
    type: unknown;
    isIncomplete?: boolean;
    typeErrors?: boolean;
    overloadsUsedForCall?: unknown[];
  }
  interface Evaluator {
    getTypeResult(node: Node): TypeResult | undefined;
    getTypeOfExpression(node: Node): TypeResult;
  }
  interface ParseApi { getChildNodes(node: Node): (Node | undefined)[]; }
  interface PositionApi {
    convertOffsetToPosition(offset: number, lines: unknown): NativeTypes.Position;
  }
  interface Location {
    path: string; line: number; column: number; end_line: number; end_column: number;
  }
  interface Argument {
    node_id: number; location: Location; category: 'simple' | 'star' | 'double_star'; name: string | null; type: number;
  }
  interface Call {
    node_id: number; location: Location; sha256: string; kind: 'function' | 'construction' | 'callable_value';
    callee_type: number; receiver_type: number | null; protocol: boolean;
    selected_signature: number; overload_index: number | null;
    arguments: Argument[]; result_type: number;
  }
}
