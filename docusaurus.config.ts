import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

const config: Config = {
  title: '知识库',
  tagline: '高性能技术文档中心',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://jlnvv-tom.github.io',
  baseUrl: '/konwledge-docs/',

  onBrokenLinks: 'warn',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'zh-Hans',
    locales: ['zh-Hans'],
  },

  stylesheets: [
    {
      href: 'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css',
      type: 'text/css',
      crossorigin: 'anonymous',
    },
  ],

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/your-repo/docs/edit/main/',
          routeBasePath: '/docs',
          sidebarCollapsible: true,
          sidebarCollapsed: false,
          remarkPlugins: [remarkMath],
          rehypePlugins: [rehypeKatex],
        },
        blog: {
          showReadingTime: true,
          feedOptions: {
            type: ['rss', 'atom'],
            xslt: true,
          },
          onInlineTags: 'warn',
          onInlineAuthors: 'warn',
          onUntruncatedBlogPosts: 'warn',
          remarkPlugins: [remarkMath],
          rehypePlugins: [rehypeKatex],
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  plugins: [
    // 本地全文搜索（无需 Algolia 申请）
    [
      '@easyops-cn/docusaurus-search-local',
      {
        hashed: true,
        language: ['zh', 'en'],
        indexDocs: true,
        indexBlog: true,
        indexPages: true,
        docsRouteBasePath: ['/docs'],
        searchBarPosition: 'right',
        searchResultLimits: 10,
        searchResultContextMaxLength: 50,
      },
    ],
  ],

  themeConfig: {
    image: 'img/docusaurus-social-card.jpg',
    colorMode: {
      defaultMode: 'light',
      respectPrefersColorScheme: true,
      disableSwitch: false,
    },
    navbar: {
      title: '知识库',
      logo: {
        alt: 'Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'tutorialSidebar',
          position: 'left',
          label: '文档',
        },
        {
          type: 'docSidebar',
          sidebarId: 'apiSidebar',
          position: 'left',
          label: 'API',
        },
        {
          type: 'docSidebar',
          sidebarId: 'knowledgeSidebar',
          position: 'left',
          label: '知识',
        },
        {to: '/blog', label: '博客', position: 'left'},
        {
          href: 'https://github.com/your-repo',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: '文档',
          items: [
            {label: '入门指南', to: '/docs/intro'},
            {label: '快速开始', to: '/docs/quick-start'},
          ],
        },
        {
          title: '社区',
          items: [
            {label: 'GitHub Issues', href: 'https://github.com/your-repo/issues'},
            {label: '讨论区', href: 'https://github.com/your-repo/discussions'},
          ],
        },
        {
          title: '更多',
          items: [
            {label: '博客', to: '/blog'},
            {label: 'GitHub', href: 'https://github.com/your-repo'},
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} 知识库. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'json', 'yaml', 'typescript', 'jsx', 'tsx', 'python', 'go', 'rust'],
    },
    // 文档目录自动生成
    tableOfContents: {
      minHeadingLevel: 2,
      maxHeadingLevel: 4,
    },
    // 版本通知条
    announcementBar: {
      id: 'announcement-bar',
      content: '🎉 知识库 v2.0 已发布，<a href="/docs/changelog">查看更新</a>',
      backgroundColor: 'var(--ifm-color-primary)',
      textColor: '#ffffff',
      isCloseable: true,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
