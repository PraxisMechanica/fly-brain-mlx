/// <reference path="./native_calls_api.d.ts" />

declare namespace NativePartials {
  interface Expression {
    node_id: number; native_kind: number; location: NativeCalls.Location; type: number;
    declarations: NativeTypes.Declaration[];
    is_incomplete: boolean | null; type_errors: boolean | null;
  }
  interface Capture { argument_node_id: number; name: string | null; expression: Expression; }
  interface Construction {
    node_id: number; location: NativeCalls.Location; sha256: string; callee_type: number;
    constructor_signature: number; wrapped: Expression; captures: Capture[];
    result_type: number; residual_signature: number;
    callee_is_incomplete: boolean | null; callee_type_errors: boolean | null;
    is_incomplete: boolean | null; type_errors: boolean | null;
  }
}
