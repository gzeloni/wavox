import type { Handle } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';

/**
 * Transparent reverse proxy: all /api/*, /dashboard/{login,callback,logout},
 * and the WebSocket upgrade path are forwarded to the FastAPI backend.
 *
 * This lets the SvelteKit container act as the single public entrypoint,
 * so cookies stay same-origin and nginx/Cloudflare only needs to forward
 * to :3000.
 */

const BACKEND = env.BACKEND_URL || 'http://web:3500';

const PROXY_PREFIXES = ['/api/', '/dashboard/login', '/dashboard/callback', '/dashboard/logout', '/docs/'];

function shouldProxy(pathname: string): boolean {
  return PROXY_PREFIXES.some((p) => pathname === p || pathname.startsWith(p));
}

export const handle: Handle = async ({ event, resolve }) => {
  const { pathname, search } = event.url;

  if (shouldProxy(pathname)) {
    const target = `${BACKEND}${pathname}${search}`;
    const headers = new Headers(event.request.headers);
    headers.delete('host');

    const init: RequestInit = {
      method: event.request.method,
      headers,
      redirect: 'manual'
    };

    if (!['GET', 'HEAD'].includes(event.request.method)) {
      init.body = await event.request.arrayBuffer();
    }

    try {
      const upstream = await fetch(target, init);
      const respHeaders = new Headers(upstream.headers);
      respHeaders.delete('transfer-encoding');
      return new Response(upstream.body, {
        status: upstream.status,
        statusText: upstream.statusText,
        headers: respHeaders
      });
    } catch (e) {
      return new Response(`Bad gateway: ${(e as Error).message}`, { status: 502 });
    }
  }

  return resolve(event);
};
