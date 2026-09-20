/**
 * A minimal static file server for the QA gates.
 *
 * The gates load each page over HTTP and not over `file:`. Two reasons:
 *
 *  1. An origin filter needs an origin. The mobile gate permits the D3 CDN
 *     and aborts every other external request. A `file:` page has no origin
 *     to compare against.
 *  2. A future page can use a root-absolute asset path. Such a path does not
 *     resolve over `file:`, because it points at the filesystem root. The
 *     page then renders without its stylesheet, and a page without a
 *     stylesheet does not overflow. The gate reports a pass and measures
 *     nothing.
 *
 * This server has no dependencies. It uses the Node standard library only.
 * Ported from the sibling `portfolio` repo on 2026-09-20.
 */
const http = require('http');
const fs = require('fs');
const path = require('path');

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpeg': 'image/jpeg',
  '.jpg': 'image/jpeg',
  '.woff2': 'font/woff2',
  '.xml': 'application/xml',
  '.txt': 'text/plain; charset=utf-8',
};

/**
 * Serve `root` on an ephemeral port. The promise resolves to
 * `{ origin, close }`.
 */
function serve(root) {
  const server = http.createServer((req, res) => {
    let rel = decodeURIComponent(req.url.split('?')[0]);
    if (rel.endsWith('/')) rel += 'index.html';
    // Keep the served path inside `root`. A `..` in the request must not
    // walk out of the site directory.
    const target = path.join(root, path.normalize(rel).replace(/^([/\\])+/, ''));
    if (!target.startsWith(path.resolve(root))) {
      res.writeHead(403).end('forbidden');
      return;
    }
    fs.readFile(target, (err, buf) => {
      if (err) {
        res.writeHead(404, { 'content-type': 'text/plain' }).end('not found');
        return;
      }
      res.writeHead(200, {
        'content-type': TYPES[path.extname(target).toLowerCase()] || 'application/octet-stream',
      });
      res.end(buf);
    });
  });

  return new Promise((resolve) => {
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      resolve({
        origin: `http://127.0.0.1:${port}`,
        close: () => new Promise((r) => server.close(r)),
      });
    });
  });
}

module.exports = { serve };
