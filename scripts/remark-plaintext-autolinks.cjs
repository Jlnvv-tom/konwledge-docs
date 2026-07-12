// 自定义 remark 插件（放在 beforeDefaultRemarkPlugins，在所有默认插件之前运行）
//
// 问题：Micromark 的 gfm-autolink-literal 在解析阶段就把正文里的裸 URL（如
// `http://localhost:5173，测试对话功能`）转成了 link 节点，而 URL 里混入了中文/全角标点，
// 导致后续 resolveMarkdownLinks 解析失败。
//
// 解决：在默认插件运行之前，把「URL 含非 ASCII 字符」的 link 节点还原为纯文本（inlineCode），
// 彻底消除后续 URL 解析错误。仅处理 autolink 类型的 link 节点（无子节点或子节点是纯文本），
// 避免影响正常的 markdown 链接 `[text](url)`。
const unistVisit = require('unist-util-visit');
const visit = unistVisit.default || unistVisit.visit || unistVisit;

const NON_ASCII = /[^\x00-\x7F]/;

function remarkFixAutolinks() {
  return (tree) => {
    visit(tree, 'link', (node, index, parent) => {
      if (!parent || typeof index !== 'number') return;
      const url = node.url || '';
      // 仅处理 URL 含非 ASCII 字符（被错误 autolink 的裸 URL）
      if (!NON_ASCII.test(url)) return;
      // 仅处理 autolink 类型：子节点为空或仅包含一个 text 节点（内容 == url）
      const children = node.children || [];
      if (
        children.length === 0 ||
        (children.length === 1 &&
          children[0].type === 'text' &&
          (children[0].value || '') === url)
      ) {
        // 还原为行内代码（显示效果接近 VitePress 的纯文本）
        parent.children[index] = { type: 'inlineCode', value: url };
      }
    });
  };
}

module.exports = remarkFixAutolinks;
