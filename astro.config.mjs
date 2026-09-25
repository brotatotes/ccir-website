import { defineConfig } from 'astro/config';
import node from '@astrojs/node';
import tina from '@tinacms/astro/integration';
import { tinaAdminDevRedirect } from '@tinacms/astro/vite';

const editing = process.env.TINA_EDITING === 'true';

export default defineConfig({
  site: 'https://ccir.brotatotes.com',
  output: 'static',
  adapter: editing ? node({ mode: 'standalone' }) : undefined,
  integrations: [tina()],
  trailingSlash: 'always',
  vite: {
    plugins: [tinaAdminDevRedirect()],
    ssr: { noExternal: ['@tinacms/astro', '@tinacms/bridge'] },
  },
});
