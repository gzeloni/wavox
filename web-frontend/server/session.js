import { createHmac, randomBytes, timingSafeEqual } from 'node:crypto';

import {
  COOKIE_SECURE,
  OAUTH_STATE_COOKIE_NAME,
  OAUTH_STATE_MAX_AGE,
  SECRET_KEY,
  SESSION_COOKIE_NAME,
  SESSION_MAX_AGE
} from './config.js';

function base64UrlEncode(value) {
  return Buffer.from(value, 'utf8').toString('base64url');
}

function base64UrlDecode(value) {
  return Buffer.from(value, 'base64url').toString('utf8');
}

function sign(base) {
  return createHmac('sha256', SECRET_KEY).update(base).digest('base64url');
}

function createSignedToken(value, issuedAt = Math.floor(Date.now() / 1000)) {
  const payload = base64UrlEncode(JSON.stringify(value));
  const base = `${payload}.${issuedAt}`;
  return `${base}.${sign(base)}`;
}

function readSignedToken(token, maxAge) {
  if (!token) return null;

  const parts = token.split('.');
  if (parts.length !== 3) return null;

  const [payload, issuedAtRaw, signature] = parts;
  const base = `${payload}.${issuedAtRaw}`;
  const expected = sign(base);

  const actualBuffer = Buffer.from(signature);
  const expectedBuffer = Buffer.from(expected);
  if (actualBuffer.length !== expectedBuffer.length) return null;
  if (!timingSafeEqual(actualBuffer, expectedBuffer)) return null;

  const issuedAt = Number(issuedAtRaw);
  if (!Number.isFinite(issuedAt)) return null;
  if (Math.floor(Date.now() / 1000) - issuedAt > maxAge) return null;

  try {
    return JSON.parse(base64UrlDecode(payload));
  } catch {
    return null;
  }
}

function cookieOptions(maxAge) {
  return {
    path: '/',
    httpOnly: true,
    sameSite: 'lax',
    secure: COOKIE_SECURE,
    maxAge
  };
}

export function parseCookieHeader(header) {
  const cookies = {};
  if (!header) return cookies;

  for (const part of header.split(';')) {
    const trimmed = part.trim();
    if (!trimmed) continue;

    const separator = trimmed.indexOf('=');
    if (separator === -1) continue;

    const key = trimmed.slice(0, separator).trim();
    const value = trimmed.slice(separator + 1).trim();
    cookies[key] = decodeURIComponent(value);
  }

  return cookies;
}

export function readSessionToken(token) {
  return readSignedToken(token, SESSION_MAX_AGE);
}

export function readOauthStateToken(token) {
  return readSignedToken(token, OAUTH_STATE_MAX_AGE);
}

export function getSessionFromCookieHeader(header) {
  const cookies = parseCookieHeader(header);
  return readSessionToken(cookies[SESSION_COOKIE_NAME] || null);
}

export function getSessionFromCookies(cookies) {
  return readSessionToken(cookies.get(SESSION_COOKIE_NAME) || null);
}

export function setSessionCookie(cookies, sessionData) {
  cookies.set(SESSION_COOKIE_NAME, createSignedToken(sessionData), cookieOptions(SESSION_MAX_AGE));
}

export function clearSessionCookie(cookies) {
  cookies.delete(SESSION_COOKIE_NAME, { path: '/' });
}

export function createOauthState() {
  return randomBytes(24).toString('base64url');
}

export function setOauthStateCookie(cookies, state) {
  cookies.set(OAUTH_STATE_COOKIE_NAME, createSignedToken({ state }), cookieOptions(OAUTH_STATE_MAX_AGE));
}

export function clearOauthStateCookie(cookies) {
  cookies.delete(OAUTH_STATE_COOKIE_NAME, { path: '/' });
}

export function verifyOauthState(cookies, state) {
  const stored = readOauthStateToken(cookies.get(OAUTH_STATE_COOKIE_NAME) || null);
  return Boolean(stored && typeof stored.state === 'string' && stored.state === state);
}
