import { writable } from 'svelte/store';
import type { Me } from '$lib/types';
import { api, UnauthorizedError } from '$lib/api';

interface SessionState {
  loading: boolean;
  me: Me | null;
  error: string | null;
}

function createSession() {
  const { subscribe, set, update } = writable<SessionState>({
    loading: true,
    me: null,
    error: null
  });

  return {
    subscribe,
    async load() {
      update((s) => ({ ...s, loading: true, error: null }));
      try {
        const me = await api.me();
        set({ loading: false, me, error: null });
      } catch (e) {
        if (e instanceof UnauthorizedError) {
          set({ loading: false, me: null, error: null });
        } else {
          set({ loading: false, me: null, error: (e as Error).message });
        }
      }
    },
    clear() {
      set({ loading: false, me: null, error: null });
    }
  };
}

export const session = createSession();
