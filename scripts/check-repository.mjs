/** Enforce repository documentation boundaries without fetching remote resources. */
import { existsSync, lstatSync, readFileSync, readdirSync } from 'node:fs';
import { basename, dirname, extname, isAbsolute, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import MarkdownIt from 'markdown-it';
import { parseDocument } from 'yaml';

const markdown = new MarkdownIt({ html: true });
const ignored = new Set(['.git', 'node_modules', 'docs', 'dist', 'build', 'artifacts', 'coverage', '.venv', '__pycache__']);
const rootPolicies = new Set(['README.md', 'AGENTS.md', 'CLAUDE.md', 'CONTRIBUTING.md', 'SECURITY.md', 'CODE_OF_CONDUCT.md', 'CHANGELOG.md']);

function allowedMarkdown(path) {
  return rootPolicies.has(path) || basename(path) === 'README.md'
    || path.startsWith('design/') || /^product\/specs\/[^/]+\.product-spec\.md$/.test(path)
    || /^skills\/[^/]+\/SKILL\.md$/.test(path)
    || path === '.github/pull_request_template.md';
}

/** Return every discovered policy error for a repository or an isolated test tree. */
export function checkRepository(root) {
  root = resolve(root);
  const errors = [];
  const files = [];
  function walk(directory) {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      if (ignored.has(entry.name)) continue;
      const absolute = resolve(directory, entry.name);
      const path = relative(root, absolute).split(sep).join('/');
      if (entry.isSymbolicLink()) errors.push(`${path}: symlink is not allowed in checked files`);
      else if (entry.isDirectory()) walk(absolute);
      else if (entry.isFile()) files.push(path);
    }
  }
  walk(root);

  function checkLink(source, href, fromRoot = false) {
    if (!href || /^(?:[a-z][a-z0-9+.-]*:|\/\/|#)/i.test(href)) return;
    let target;
    try {
      const path = decodeURIComponent(href.split(/[?#]/, 1)[0]);
      target = resolve(fromRoot ? root : dirname(resolve(root, source)), path);
    } catch {
      errors.push(`${source}: malformed link ${href}`);
      return;
    }
    const local = relative(root, target);
    if (local === '..' || local.startsWith(`..${sep}`) || isAbsolute(local)) {
      errors.push(`${source}: link escapes repository: ${href}`);
      return;
    }
    let ancestor = target;
    while (ancestor !== root) {
      if (existsSync(ancestor) && lstatSync(ancestor).isSymbolicLink()) {
        errors.push(`${source}: link follows a symlink: ${href}`);
        return;
      }
      ancestor = dirname(ancestor);
    }
    if (!existsSync(target)) errors.push(`${source}: missing link target: ${href}`);
  }

  function yaml(source, value) {
    const parsed = parseDocument(value, { uniqueKeys: true });
    for (const error of parsed.errors) errors.push(`${source}: ${error.message}`);
    return parsed.errors.length ? null : parsed.toJSON();
  }

  for (const path of files) {
    const extension = extname(path).toLowerCase();
    if (!['.md', '.json', '.yml', '.yaml'].includes(extension)) continue;
    const content = readFileSync(resolve(root, path), 'utf8');
    if (extension === '.json') {
      try { JSON.parse(content); }
      catch { errors.push(`${path}: invalid JSON`); }
      continue;
    }
    if (extension === '.yml' || extension === '.yaml') {
      yaml(path, content);
      continue;
    }
    if (!allowedMarkdown(path)) errors.push(`${path}: Markdown location is not allowed`);
    if (path === 'SECURITY.md' && !content.includes('core-server-client-v1')) {
      errors.push('SECURITY.md: describe core-server-client-v1');
    }
    if (/^clients\/(chatgpt|claude-code|claude-desktop|codex)\/README\.md$/.test(path)
        && !content.includes('../../SECURITY.md#remove-retained-data')) {
      errors.push(`${path}: link Remove retained data in SECURITY.md`);
    }
    if (content.includes('\u2014') && path !== 'CODE_OF_CONDUCT.md') errors.push(`${path}: replace em dashes with plain punctuation`);
    if (path === 'CLAUDE.md' && (content.trim() !== '@AGENTS.md' || !existsSync(resolve(root, 'AGENTS.md')))) {
      errors.push('CLAUDE.md: import AGENTS.md as the single instruction source');
    }
    function visit(tokens) {
      for (const token of tokens) {
        if (token.type === 'link_open') checkLink(path, token.attrGet('href'));
        if (token.type === 'image') checkLink(path, token.attrGet('src'));
        if (token.type.startsWith('html_')) {
          for (const match of token.content.matchAll(/<img\b[^>]*\bsrc=["']([^"']+)["']/gi)) checkLink(path, match[1]);
        }
        if (token.type === 'fence' && token.info.trim() === 'productspec-related-artifacts') {
          const artifacts = yaml(path, token.content);
          if (Array.isArray(artifacts)) for (const artifact of artifacts) {
            if (typeof artifact?.url === 'string') checkLink(path, artifact.url, true);
          }
        }
        if (token.children) visit(token.children);
      }
    }
    visit(markdown.parse(content, {}));
  }
  return errors;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const errors = checkRepository(process.cwd());
  if (errors.length) {
    for (const error of errors) process.stderr.write(`${error}\n`);
    process.exitCode = 1;
  } else {
    process.stdout.write('Repository policy, local links, and JSON/YAML syntax: OK\n');
  }
}
