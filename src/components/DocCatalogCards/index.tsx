import type {ReactNode} from 'react';
import {useCurrentSidebarSiblings, filterDocCardListItems} from '@docusaurus/plugin-content-docs/client';
import Link from '@docusaurus/Link';
import type {PropSidebarItem} from '@docusaurus/plugin-content-docs';
import styles from './styles.module.css';

type SidebarItem = PropSidebarItem & {
  docId?: string;
  href?: string;
  label?: string;
};

function CatalogCard({item}: {item: SidebarItem}) {
  const label = (item as any).label || (item as any).docId || '未命名';
  const href = (item as any).href || '#';
  const isCategory = item.type === 'category';

  return (
    <Link to={href} className={styles.cardLink}>
      <div className={styles.card}>
        <div className={styles.cardIcon}>
          {isCategory ? '📂' : '📄'}
        </div>
        <div className={styles.cardBody}>
          <div className={styles.cardTitle}>{label}</div>
        </div>
        <div className={styles.cardArrow}>→</div>
      </div>
    </Link>
  );
}

export default function DocCatalogCards(): ReactNode {
  const items = useCurrentSidebarSiblings() as SidebarItem[];
  const filteredItems = filterDocCardListItems(items) as SidebarItem[];

  // 过滤掉 index 页面自身
  const articleItems = filteredItems.filter((item) => {
    if (item.type === 'doc' && item.docId?.endsWith('/index')) {
      return false;
    }
    return true;
  });

  if (articleItems.length === 0) {
    return (
      <div className={styles.empty}>
        <p>📚 本系列暂无文章</p>
      </div>
    );
  }

  return (
    <div className={styles.cardGrid}>
      {articleItems.map((item, index) => (
        <CatalogCard key={index} item={item} />
      ))}
    </div>
  );
}
