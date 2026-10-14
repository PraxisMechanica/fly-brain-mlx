// @ts-check
/// <reference path="./native_types_node.d.ts" />
import {realpathSync} from 'node:fs';
import {fail} from './native_types_values.mjs';
/** @param {import('./native_sources_context.mjs').Context} context */
export function projectSources(context) {
  const {ts, program, sources} = context;
  const checker = program.getTypeChecker();
  /** @param {import('../../node_modules/.pnpm/typescript@5.9.3/node_modules/typescript/lib/typescript.js').Node} node */
  function location(node) {
    const source = node.getSourceFile();
    const start = source.getLineAndCharacterOfPosition(node.getStart(source));
    const end = source.getLineAndCharacterOfPosition(node.getEnd());
    return {path: realpathSync(source.fileName), line: start.line + 1, column: start.character,
      end_line: end.line + 1, end_column: end.character};
  }
  /** @param {import('../../node_modules/.pnpm/typescript@5.9.3/node_modules/typescript/lib/typescript.js').Symbol} symbol */
  function target(symbol) {
    const resolved = symbol.flags & ts.SymbolFlags.Alias ? checker.getAliasedSymbol(symbol) : symbol;
    if (!resolved.declarations?.length) fail(`native symbol has no resolved declaration: ${symbol.name}`);
    return {name: resolved.name, flags: resolved.flags, declarations: resolved.declarations.map(location)};
  }
  const files = [...sources].map(([path, sha256]) => {
    const source = program.getSourceFile(path);
    if (!source || !source.statements.length) fail(`native populated source is empty: ${path}`);
    /** @type {NativeTypes.RecordValue[]} */
    const declarations = [];
    /** @type {NativeTypes.RecordValue[]} */
    const bindings = [];
    /** @type {NativeTypes.RecordValue[]} */
    const imports = [];
    /** @type {Set<import('../../node_modules/.pnpm/typescript@5.9.3/node_modules/typescript/lib/typescript.js').Node>} */
    const visited = new Set();
    /** @param {import('../../node_modules/.pnpm/typescript@5.9.3/node_modules/typescript/lib/typescript.js').Node} node */
    function visit(node) {
      if (visited.has(node)) return;
      visited.add(node);
      if (ts.isIdentifier(node) || ts.isStringLiteralLike(node)) {
        const symbol = checker.getSymbolAtLocation(node);
        const own = symbol?.declarations?.find((declaration) => ts.getNameOfDeclaration(declaration) === node);
        if (symbol && own) {
          const record = {name: node.text, kind: ts.SyntaxKind[own.kind], location: location(node), target: target(symbol)};
          declarations.push(record);
          if (ts.isVariableDeclaration(own) || ts.isParameter(own) || ts.isBindingElement(own) || ts.isImportSpecifier(own) || ts.isImportClause(own) || ts.isNamespaceImport(own)) bindings.push(record);
        }
      }
      if (ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) {
        const specifier = node.moduleSpecifier;
        if (specifier) {
          const symbol = checker.getSymbolAtLocation(specifier);
          if (!symbol) fail(`native module import is unresolved: ${specifier.getText(source)}`);
          imports.push({specifier: specifier.getText(source), location: location(specifier), target: target(symbol), type_only: ts.isImportDeclaration(node) ? !!node.importClause?.isTypeOnly : node.isTypeOnly});
        }
      }
      if (ts.isImportTypeNode(node) && ts.isLiteralTypeNode(node.argument)) {
        const specifier = node.argument.literal;
        const symbol = checker.getSymbolAtLocation(specifier);
        if (!symbol) fail(`native type import is unresolved: ${specifier.getText(source)}`);
        imports.push({specifier: specifier.getText(source), location: location(specifier), target: target(symbol), type_only: true});
      }
      ts.forEachChild(node, visit);
      for (const tag of ts.getJSDocTags(node)) visit(tag);
    }
    visit(source);
    const module = checker.getSymbolAtLocation(source);
    const exports = module ? checker.getExportsOfModule(module).map((symbol) => ({name: symbol.name, target: target(symbol)})) : [];
    return {path, sha256, declarations, bindings, imports, exports};
  });
  return files;
}
