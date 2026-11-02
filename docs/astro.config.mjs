// @ts-check
// The shared max-models docs setup (@max-models/starlight-theme): served at
// https://max-models.github.io/methodcard/, with math, the API reference and a link check.
import { defineDocs } from '@max-models/starlight-theme';

export default defineDocs({
	repo: 'methodcard',
	title: 'methodcard',
	description: 'The math of each numerical method, declared once and shown in its docs and tests.',
	pythonPackage: 'methodcard',
	nav: [
		{ label: 'Getting started', link: '/getting-started/installation/' },
		{ label: 'Examples', link: '/examples/' },
		{ label: 'Development', link: '/development/docs/' },
		{ label: 'API', link: '/api/methodcard/' },
	],
	sidebar: [
		{
			label: 'Getting started',
			items: [
				{ label: 'Installation', slug: 'getting-started/installation' },
				{ label: 'Quickstart', slug: 'getting-started/quickstart' },
			],
		},
		{
			label: 'Examples',
			items: [
				{ autogenerate: { directory: 'examples' } },
			],
		},
		{
			label: 'Development',
			items: [
				{ label: 'Design', slug: 'development/design' },
				{ label: 'Building the docs', slug: 'development/docs' },
				{ label: 'Publishing', slug: 'development/publishing' },
			],
		},
	],
});
