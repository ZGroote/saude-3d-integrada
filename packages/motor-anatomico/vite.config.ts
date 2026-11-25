import { fileURLToPath } from 'node:url';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

const aqui = (caminho: string) => fileURLToPath(new URL(caminho, import.meta.url));

// Só para a demo. publicDir = atlas/ do repositório, servido na raiz (/bp3d-m/4.0-1/…).
export default defineConfig(({ mode }) => ({
  plugins: [react()],
  root: mode === 'test' ? aqui('.') : aqui('demo'),
  publicDir: mode === 'test' ? false : aqui('../../atlas'),
}));
