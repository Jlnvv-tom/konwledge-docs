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
              to="/docs/history-humanities">
              开始探索 →
            </Link>
            <Link
              className={clsx('button button--secondary button--lg', styles.btnOutline)}
              to="/docs/ai-practice">
              AI 实战
            </Link>
          </div>
        </div>
        <div className={styles.heroBadge}>
          <span className={styles.badgeItem}>⚡️ 7 大分类</span>
          <span className={styles.badgeItem}>🔍 全文搜索</span>
          <span className={styles.badgeItem}>🌙 暗色模式</span>
          <span className={styles.badgeItem}>📱 响应式</span>
        </div>
      </div>
    </header>
  );
}

type CategoryItem = {
  icon: string;
  title: string;
  description: string;
  link: string;
  color: string;
};

const categories: CategoryItem[] = [
  {
    icon: '📜',
    title: '历史与人文',
    description: '大明通史、政府与法治、经典书籍、自然奇观、认知偏差',
    link: '/docs/history-humanities',
    color: '#8B5E3C',
  },
  {
    icon: '💰',
    title: '商业与经济',
    description: '跨境电商、经济学原理、中国经济、科技公司、管理模型',
    link: '/docs/business-economics',
    color: '#2E7D32',
  },
  {
    icon: '🤖',
    title: 'AI 应用与实战',
    description: 'Agent 开发、AI 绘画/视频/语音、产品经理、LLM 研究',
    link: '/docs/ai-practice',
    color: '#6A1B9A',
  },
  {
    icon: '🐍',
    title: 'Python 与爬虫',
    description: 'Python 学习、实战训练、爬虫、LLM 开发、LangChain',
    link: '/docs/python-crawler',
    color: '#1565C0',
  },
  {
    icon: '⚙️',
    title: '后端与数据库',
    description: 'Go 语言、MySQL、Redis、FastAPI、CDP',
    link: '/docs/backend-database',
    color: '#E65100',
  },
  {
    icon: '🎨',
    title: '前端工程',
    description: 'Chrome 原理、Canvas、Next.js、React Native、Electron',
    link: '/docs/frontend-engineering',
    color: '#C2185B',
  },
  {
    icon: '📚',
    title: '生活与百科',
    description: '猫、育儿、英语、程序员面试、互联网未来、技能之书',
    link: '/docs/life-encyclopedia',
    color: '#00838F',
  },
];

function CategoryCard({item}: {item: CategoryItem}) {
  return (
    <div className="col col--4 margin-bottom--lg">
      <Link to={item.link} className={styles.featureCard} style={{textDecoration: 'none', display: 'block'}}>
        <div className={styles.featureIcon} style={{color: item.color}}>{item.icon}</div>
        <Heading as="h3" className={styles.featureTitle}>
          {item.title}
        </Heading>
        <p className={styles.featureDesc}>{item.description}</p>
        <div className={styles.featureLink} style={{color: item.color}}>
          进入分类 →
        </div>
      </Link>
    </div>
  );
}

function CategoriesSection() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {categories.map((item, idx) => (
            <CategoryCard key={idx} item={item} />
          ))}
        </div>
      </div>
    </section>
  );
}

/* 统计数据条 */
function StatsSection() {
  const stats = [
    {value: '7', label: '大分类'},
    {value: '56+', label: '子系列'},
    {value: '700+', label: '文章'},
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

/* CTA 行动号召 */
function CTASection() {
  return (
    <section className={styles.cta}>
      <div className="container text--center">
        <Heading as="h2" className={styles.ctaTitle}>
          准备好开始了吗？
        </Heading>
        <p className={styles.ctaDesc}>
          选择一个分类，进入卡片导航页，每张卡片对应一篇文章
        </p>
        <Link
          className="button button--primary button--lg"
          to="/docs/ai-practice">
          浏览 AI 实战 →
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
        <CategoriesSection />
        <StatsSection />
        <CTASection />
      </main>
    </Layout>
  );
}
