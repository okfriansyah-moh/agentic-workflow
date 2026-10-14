import parser from '@typescript-eslint/parser';
import svelte from 'eslint-plugin-svelte';
import policy from '../../../profiles/web/eslint.config.mjs';
export default [
  { files: ['**/*.ts'], languageOptions: { parser } },
  ...svelte.configs['flat/recommended'],
  { files: ['**/*.svelte'], languageOptions: { parserOptions: { parser } } },
  ...policy,
];
