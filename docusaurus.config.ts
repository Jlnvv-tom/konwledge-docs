import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
// 自定义插件：把被 remark-gfm 错误 autolink 的裸 URL（含中文/全角标点）还原为纯文本
import remarkPlaintextAutolinks from './scripts/remark-plaintext-autolinks.cjs';

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
  // 迁移自 VitePress 的 .md 含大量 { } 字面量：detect 让 .md 走纯 Markdown、.mdx 仍走 MDX，
  // 避免 MDX 把 { } 当成 JSX 表达式而构建报错
  markdown: {
    format: 'detect',
    hooks: {
      onBrokenMarkdownLinks: 'warn',
      // 源文档含 55 处未填实的图片占位符「图片URL」，仅告警不阻断构建
      onBrokenMarkdownImages: 'warn',
    },
  },

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
          editUrl: 'https://github.com/Jlnvv-tom/konwledge-docs/edit/master/',
          routeBasePath: '/docs',
          sidebarCollapsible: true,
          sidebarCollapsed: false,
          remarkPlugins: [remarkMath, remarkPlaintextAutolinks],
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
          remarkPlugins: [remarkMath, remarkPlaintextAutolinks],
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
        {
          type: 'docSidebar',
          sidebarId: 'notesSidebar',
          position: 'left',
          label: '笔记',
        },
        {to: '/blog', label: '博客', position: 'left'},
        {
          href: 'https://github.com/Jlnvv-tom/konwledge-docs',
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
            {label: 'GitHub Issues', href: 'https://github.com/Jlnvv-tom/konwledge-docs/issues'},
            {label: '讨论区', href: 'https://github.com/Jlnvv-tom/konwledge-docs/discussions'},
          ],
        },
        {
          title: '更多',
          items: [
            {label: '博客', to: '/blog'},
            {label: 'GitHub', href: 'https://github.com/Jlnvv-tom/konwledge-docs'},
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
