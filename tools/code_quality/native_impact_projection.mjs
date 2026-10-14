// @ts-check
/// <reference path="../architecture/native_types_node.d.ts" />
import {realpathSync} from 'node:fs';
import {fail} from '../architecture/native_types_values.mjs';
/** @param {import('./native_impact_context.mjs').Context} context */
export function project(context) {
  const {ts, parsed, program, host, builder, sources} = context;
  const checker = program.getTypeChecker();
  /** @type {string[]} */
  const globals = [];
  const graph = Object.fromEntries([...sources.keys()].map(path => {
    const source = program.getSourceFile(path);
    if (!source) fail(`native compiler omitted source: ${path}`);
    let global = !ts.isExternalModule(source) && source.statements.some(statement => !ts.isModuleDeclaration(statement) || !ts.isStringLiteral(statement.name));
    /** @type {Set<import('../../node_modules/.pnpm/typescript@5.9.3/node_modules/typescript/lib/typescript.js').Node>} */
    const visited = new Set();
    /** @param {import('../../node_modules/.pnpm/typescript@5.9.3/node_modules/typescript/lib/typescript.js').Node} node */
    function visit(node) {
      if (visited.has(node)) return;
      visited.add(node);
      /** @type {import('../../node_modules/.pnpm/typescript@5.9.3/node_modules/typescript/lib/typescript.js').Node | undefined} */
      let module;
      if (ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) module = node.moduleSpecifier;
      if (ts.isImportTypeNode(node)) module = ts.isLiteralTypeNode(node.argument) ? node.argument.literal : node.argument;
      if (ts.isExternalModuleReference(node)) module = node.expression;
      if (ts.isCallExpression(node) && node.expression.kind === ts.SyntaxKind.ImportKeyword) {
        module = node.arguments[0];
        if (!module || node.arguments.length !== 1) fail(`unproved native module dependency: ${path}:${node.getStart(source)}`);
      }
      if (module && (!ts.isStringLiteralLike(module) || !checker.getSymbolAtLocation(module)?.declarations?.length)) fail(`unresolved or unsupported native module dependency: ${path}:${module.getStart(source)}`);
      if (ts.isModuleDeclaration(node) && node.flags & ts.NodeFlags.GlobalAugmentation) global = true;
      ts.forEachChild(node, visit);
      for (const tag of ts.getJSDocTags(node)) visit(tag);
    }
    visit(source);
    for (const reference of source.referencedFiles) {
      const referenced = ts.resolveTripleslashReference(reference.fileName, path);
      if (!program.getSourceFile(referenced)) fail(`missing native referenced input: ${path}:${reference.fileName}`);
    }
    for (const reference of source.typeReferenceDirectives) {
      if (!ts.resolveTypeReferenceDirective(reference.fileName, path, parsed.options, host, undefined, undefined, reference.resolutionMode).resolvedTypeReferenceDirective) fail(`unresolved native type reference: ${path}:${reference.fileName}`);
    }
    const dependencies = builder.getAllDependencies(source).map(name => realpathSync(name)).filter(name => sources.has(name));
    if (global) globals.push(path);
    return [path, dependencies];
  }));
  return {graph, globals};
}
