#!/usr/bin/env sh

# 确保脚本抛出遇到的错误
set -e

# 生成静态文件（Docusaurus 构建到 build 目录）
npm run build

# 进入生成的文件夹
cd build

# 初始化临时仓库并提交
git init
git add -A
git commit -m 'deploy'

# 发布到 https://<USERNAME>.github.io/<REPO> 的 gh-pages 分支
git push -f https://github.com/Jlnvv-tom/konwledge-docs.git master:gh-pages

cd -
