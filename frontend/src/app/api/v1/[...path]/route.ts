// Same-origin API proxy.
//
// The browser talks only to this origin (/api/v1/*); this route pipes the
// request to the Django backend and streams the response back. This removes
// CORS, preflight OPTIONS traffic, and the cross-origin cookie/connection
// failures that caused flaky login, refresh->/login on reload, and Firefox
// 'NS_ERROR_CONNECTION_REFUSE' against an IPv4-only backend.
//
// A trailing slash is always appended because Django runs with APPEND_SLASH
// and cannot redirect POST bodies (RuntimeError). Raw streaming is preserved
// so the SSE /chat/stream/ endpoint token-streams through the proxy.

import { NextRequest } from 'next/server';

export const runtime = 'nodejs';

const BACKEND_ORIGIN = (() => {
  const configured = process.env.BACKEND_ORIGIN;
  if (configured) {
    return configured.replace(/\/+$/, '');
  }
  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (apiBase) {
    try {
      return new URL(apiBase).origin;
    } catch {
      // fall through to default
    }
  }
  return 'http://localhost:8000';
})();

// Headers that must not hop through a proxy.
const HOP_BY_HOP = new Set([
  'connection',
  'keep-alive',
  'proxy-authenticate',
  'proxy-authorization',
  'te',
  'trailer',
  'transfer-encoding',
  'upgrade',
  'host',
  'content-length',
]);

async function handle(request: NextRequest, segments: string[]) {
  const target = `${BACKEND_ORIGIN}/api/v1/${segments.join('/')}/`;

  const headers = new Headers();
  request.headers.forEach((value, key) => {
    if (!HOP_BY_HOP.has(key.toLowerCase())) {
      headers.set(key, value);
    }
  });
  headers.delete('x-forwarded-host');
  headers.delete('x-forwarded-proto');

  const isBodyless = request.method === 'GET' || request.method === 'HEAD';
  // Buffer the incoming body once. Passing the raw ReadableStream to undici
  // silently dropped it in Next 16 route handlers, so materialize a Blob
  // (still streams efficiently and works for large uploads).
  const body = isBodyless ? undefined : await request.blob();

  const upstream = await fetch(target, {
    method: request.method,
    headers,
    body,
    redirect: 'manual',
  });

  const responseHeaders = new Headers();
  upstream.headers.forEach((value, key) => {
    if (!HOP_BY_HOP.has(key.toLowerCase())) {
      responseHeaders.set(key, value);
    }
  });
  // CORS headers are meaningless now that the API is same-origin.
  responseHeaders.delete('access-control-allow-origin');
  responseHeaders.delete('access-control-allow-credentials');
  responseHeaders.delete('vary');

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: responseHeaders,
  });
}

export const GET = (req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) =>
  ctx.params.then(({ path }) => handle(req, path));
export const POST = (req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) =>
  ctx.params.then(({ path }) => handle(req, path));
export const PUT = (req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) =>
  ctx.params.then(({ path }) => handle(req, path));
export const PATCH = (req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) =>
  ctx.params.then(({ path }) => handle(req, path));
export const DELETE = (req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) =>
  ctx.params.then(({ path }) => handle(req, path));
export const OPTIONS = (req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) =>
  ctx.params.then(({ path }) => handle(req, path));