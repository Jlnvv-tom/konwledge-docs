import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import styles from './index.module.css';

/* ===== 自定义首页 ===== */
function HeroSection() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={styles.heroBanner}>
      <div className="container">
        <div className={styles.heroContent}>
          <Heading as="h1" className={styles.heroTitle}>
            {siteConfig.title}
          </Heading>
          <p className={styles.heroSubtitle}>{siteConfig.tagline}</p>
          <div className={styles.heroButtons}>
            <Link
              className="button button--primary button--lg"
              to="/docs/intro">
              快速开始 →
            </Link>
            <Link
              className={clsx('button button--secondary button--lg', styles.btnOutline)}
              to="/docs/quick-start">
              查看文档
            </Link>
          </div>
        </div>
        <div className={styles.heroBadge}>
          <span className={styles.badgeItem}>⚡️ 构建不 OOM</span>
          <span className={styles.badgeItem}>🔍 全文搜索</span>
          <span className={styles.badgeItem}>🌙 暗色模式</span>
          <span className={styles.badgeItem}>📱 响应式</span>
        </div>
      </div>
    </header>
  );
}

type FeatureItem = {
  title: string;
  icon: string;
  description: string;
  link?: string;
};

const features: FeatureItem[] = [
  {
    title: '纯 Markdown 友好',
    icon: '📝',
    description: '直接将 .md 文件放入 docs 目录，无需修改文件后缀。支持 frontmatter、代码高亮、Admonition 容器等常用语法。',
    link: '/docs/intro',
  },
  {
    title: '构建内存安全',
    icon: '🛡️',
    description: 'Docusaurus 逐页编译渲染，不会像 VitePress 那样将所有文档全量加载到内存。上千份文档也能稳定构建。',
    link: '/docs/quick-start',
  },
  {
    title: '本地全文搜索',
    icon: '🔍',
    description: '内置 @easyops-cn/docusaurus-search-local 插件，支持中英文分词，无需申请 Algolia，开箱即用。',
  },
  {
    title: '定制主题',
    icon: '🎨',
    description: '靛蓝主色调 + 毛玻璃导航栏 + 渐变 Hero + 卡片悬浮效果，通过 CSS 变量覆盖即可实现深度定制。',
  },
  {
    title: 'TypeScript 支持',
    icon: '📘',
    description: '项目使用 TypeScript 模板，配置文件、组件、插件均有类型提示，开发体验更好。',
  },
  {
    title: '暗色模式',
    icon: '🌙',
    description: '自动跟随系统偏好，也可手动切换。暗色主题专为长时间阅读优化，减少眼部疲劳。',
  },
];

function FeatureCard({feature}: {feature: FeatureItem}) {
  return (
    <div className="col col--4 margin-bottom--lg">
      <div className={styles.featureCard}>
        <div className={styles.featureIcon}>{feature.icon}</div>
        <Heading as="h3" className={styles.featureTitle}>
          {feature.title}
        </Heading>
        <p className={styles.featureDesc}>{feature.description}</p>
        {feature.link && (
          <Link to={feature.link} className={styles.featureLink}>
            了解更多 →
          </Link>
        )}
      </div>
    </div>
  );
}

function FeaturesSection() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {features.map((feature, idx) => (
            <FeatureCard key={idx} feature={feature} />
          ))}
        </div>
      </div>
    </section>
  );
}

/* 统计数据条 */
function StatsSection() {
  const stats = [
    {value: '500+', label: '文档页面'},
    {value: '<2s', label: '首屏加载'},
    {value: '0', label: 'OOM 风险'},
    {value: '100', label: 'Lighthouse 评分'},
  ];
  return (
    <section className={styles.stats}>
      <div className="container">
        <div className="row">
          {stats.map((stat, idx) => (
            <div key={idx} className="col col--3 text--center">
              <div className={styles.statValue}>{stat.value}</div>
              <div className={styles.statLabel}>{stat.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* 代码示例区 */
function CodeShowcaseSection() {
  return (
    <section className={styles.codeShowcase}>
      <div className="container">
        <div className="row align-items--center">
          <div className="col col--5">
            <Heading as="h2" className={styles.sectionTitle}>
              Markdown 即所见
            </Heading>
            <p className={styles.sectionDesc}>
              标准 Markdown 语法，无需学习新东西。支持代码高亮、Admonition 容器、表格、图片等全部常用功能。
            </p>
            <ul className={styles.benefitList}>
              <li>✅ 标准 Markdown 语法，零学习成本</li>
              <li>✅ Admonition 容器（tip / info / warning / danger）</li>
              <li>✅ 多语言代码高亮（含 Bash、JSON、YAML、TS 等）</li>
              <li>✅ frontmatter 元数据支持</li>
            </ul>
          </div>
          <div className="col col--7">
            <div className={styles.codeBlock}>
              <pre>
                <code>{`---
title: 快速开始
description: 5 分钟上手知识库
---

## 安装

\`\`\`bash
npm install
\`\`\`

:::tip 提示
确保 Node.js >= 20
:::

| 特性 | 支持状态 |
|------|---------|
| Markdown | ✅ |
| 搜索 | ✅ |
| 暗色模式 | ✅ |`}</code>
              </pre>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* CTA 行动号召 */
function CTASection() {
  return (
    <section className={styles.cta}>
      <div className="container text--center">
        <Heading as="h2" className={styles.ctaTitle}>
          准备好开始了吗？
        </Heading>
        <p className={styles.ctaDesc}>
          将你的 Markdown 文档放入 docs 目录，运行 npm start 即可预览
        </p>
        <Link
          className="button button--primary button--lg"
          to="/docs/intro">
          浏览文档 →
        </Link>
      </div>
    </section>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title="首页"
      description="高性能技术文档中心 - 基于 Docusaurus 构建">
      <HeroSection />
      <main>
        <FeaturesSection />
        <StatsSection />
        <CodeShowcaseSection />
        <CTASection />
      </main>
    </Layout>
  );
}
