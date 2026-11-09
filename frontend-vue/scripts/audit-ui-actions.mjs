// Static action inventory; transport and durable outcomes require separate tests.
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { parse, compileScript } = require('vue/compiler-sfc');
const { baseParse } = createRequire(require.resolve('vue/compiler-sfc'))('@vue/compiler-dom');
import { existsSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
const root = path.resolve(import.meta.dirname, '..');
function files(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap(e => e.isDirectory() ? files(path.join(dir, e.name)) : e.name.endsWith('.vue') ? [path.join(dir, e.name)] : []);
}
const rows = [];
const unresolved = [];
for (const file of files(path.join(root, 'src'))) {
  const source = readFileSync(file, 'utf8');
  const { descriptor } = parse(source);
  if (!descriptor.template) continue;
  let scriptBindings;
  if (descriptor.scriptSetup) {
    try {
      scriptBindings = compileScript(descriptor, { id: file, fs: { fileExists: existsSync, readFile: p => readFileSync(p, 'utf8') } }).bindings;
    } catch { /* Type imports may require build context; leave outcome unverified. */ }
  }
  const ast = baseParse(descriptor.template.content);
  function walk(node, form = '') {
    if (node.type !== 1) { for (const child of node.children || []) walk(child, form); return; }
    const attrs = Object.fromEntries(node.props.filter(p => p.type === 6).map(p => [p.name, p.value?.content || '']));
    const events = node.props.filter(p => p.type === 7 && p.name === 'on').map(p => `${p.arg?.content || '*'}: ${p.exp?.content || ''}`);
    const bindings = node.props.filter(p => p.type === 7 && p.name === 'bind').map(p => `${p.arg?.content}: ${p.exp?.content}`);
    if (scriptBindings) {
      for (const prop of node.props.filter(p => p.type === 7 && p.name === 'on')) {
        const name = prop.exp?.content.match(/^\s*([A-Za-z_$][\w$]*)\s*(?:\(|$)/)?.[1];
        if (name && !scriptBindings[name] && !['$emit', 'emit', 'console'].includes(name)) {
          unresolved.push([path.relative(root, file), node.loc.start.line + descriptor.template.loc.start.line - 1, name]);
        }
      }
    }
    if (node.tag === 'form') form = events.join(' | ');
    const interactive = /^(button|UButton|a|router-link|RouterLink|form)$/.test(node.tag) || events.length;
    if (interactive) {
      const text = node.loc.source.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 160);
      const route = attrs.href || attrs.to || bindings.find(b => /^(to|href):/.test(b)) || '';
      const wiring = events.join(' | ') || route || (attrs.type !== 'button' && form ? `form: ${form}` : '');
      const disabled = 'disabled' in attrs || bindings.some(b => b.startsWith('disabled:'));
      rows.push([path.relative(root, file), node.loc.start.line + descriptor.template.loc.start.line - 1, node.tag, attrs['aria-label'] || attrs.title || text, wiring, disabled ? 'conditional/static' : '', wiring ? 'bound; outcome needs verification' : disabled ? 'disabled; review availability' : 'REVIEW missing action', 'not exercised by static audit']);
    }
    for (const child of node.children || []) walk(child, form);
  }
  walk(ast);
}
process.exitCode = missingActions();
function missingActions() { return rows.some(r => r[6].startsWith('REVIEW')) || unresolved.length ? 1 : 0; }
const clean = x => String(x).replace(/[\t\r\n]+/g, ' ');
const output = path.resolve(root, '../docs/plans/UI_ACTION_INVENTORY.tsv');
writeFileSync(output, [['file','line','element','label','binding','disabled','static_status','verification'], ...rows].map(r => r.map(clean).join('\t')).join('\n') + '\n');
const missing = rows.filter(r => r[6].startsWith('REVIEW'));
console.log(JSON.stringify({ controls: rows.length, missing: missing.length, unresolvedHandlers: unresolved, inventory: output }));
for (const row of missing) console.log(row.slice(0, 5).join('\t'));
