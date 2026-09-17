/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  readonly VITE_APP_NAME?: string;
  readonly VITE_APP_ENV?: string;
  readonly VITE_ENABLE_QUERY_DEVTOOLS?: string;
  readonly VITE_GALA_POLLING_INTERVAL?: string;
  readonly VITE_API_TIMEOUT?: string;
  readonly VITE_DEV_API_PROXY_TARGET?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare const __APP_ENV__: string;
declare const __APP_NAME__: string;
