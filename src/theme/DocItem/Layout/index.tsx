import React, {type ReactNode} from 'react';
import Layout from '@theme-original/DocItem/Layout';
import type {Props} from '@theme/DocItem/Layout';
import styles from './styles.module.css';

/**
 * 文档页布局覆盖：在每篇文档顶部添加"返回顶部"快捷按钮
 * 同时添加文档底部反馈区
 */
export default function LayoutWrapper(props: Props): ReactNode {
  return (
    <>
      <Layout {...props} />
      <div className={styles.feedbackSection}>
        <div className="container">
          <div className={styles.feedbackInner}>
            <span className={styles.feedbackText}>
              这篇文档对你有帮助吗？
            </span>
            <div className={styles.feedbackButtons}>
              <a
                href="https://github.com/your-repo/docs/issues/new"
                target="_blank"
                rel="noopener noreferrer"
                className={styles.feedbackBtn}>
                📝 提交反馈
              </a>
              <a
                href="https://github.com/your-repo/docs/edit/main/"
                target="_blank"
                rel="noopener noreferrer"
                className={styles.feedbackBtn}>
                ✏️ 编辑此页
              </a>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
