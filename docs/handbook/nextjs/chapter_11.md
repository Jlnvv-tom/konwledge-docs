# 第11章 静态资源、图片、字体与媒体优化

一个首屏加载3秒的网站，用户流失率比1秒的网站高50%。而3秒里有2秒可能花在图片上。Next.js的Image组件和next/font能让你的资源加载时间砍掉一半，但你得知道怎么配。

我是怕浪猫，一个对性能优化有强迫症的全栈开发者。这章把Next.js静态资源优化的每个环节拆开讲——从图片到字体，从打包到压缩，帮你把首屏加载压到极限。

## 11.1 Next.js静态资源引入规范

### 11.1.1 public/目录：直接URL访问的静态文件

放在`public/`目录下的文件可以通过URL直接访问：

```
public/
├── images/
│   ├── logo.png        → /images/logo.png
│   └── hero.jpg        → /images/hero.jpg
├── favicon.ico         → /favicon.ico
├── robots.txt          → /robots.txt
└── sitemap.xml         → /sitemap.xml
```

```tsx
// 使用
export default function Header() {
  return <img src="/images/logo.png" alt="Logo" />
  // 或者用next/image
  // return <Image src="/images/logo.png" width={120} height={40} alt="Logo" />
}
```

public目录适合：favicon、robots.txt、sitemap.xml、不需要构建处理的静态文件。

### 11.1.2 import方式引入：模块化资源管理

```tsx
import logo from '@/assets/logo.png'
import heroImage from '@/assets/hero.jpg'

export default function Header() {
  return (
    <div>
      <Image src={logo} alt="Logo" />
      <Image src={heroImage} alt="Hero" priority />
    </div>
  )
}
```

import方式的优势：构建时自动处理文件哈希、自动压缩、Tree Shaking友好。

> import和public两种方式的本质区别：import走构建管线，有压缩有哈希有优化；public是原始文件直出。能用import就用import，public留给必须直出的文件。

### 11.1.3 静态资源的构建处理：哈希命名与CDN

Next.js构建时自动给import的资源加哈希：

```
开发环境：/_next/static/media/logo.png
生产环境：/_next/static/media/logo.a1b2c3d4.png (带哈希)
```

哈希命名的意义：文件内容不变则哈希不变，浏览器可以永久缓存。内容变了哈希变，浏览器自动拉新文件。

配置CDN：

```javascript
// next.config.js
const nextConfig = {
  assetPrefix: 'https://cdn.example.com',
  // 或者按环境配置
  // assetPrefix: process.env.NODE_ENV === 'production' ? 'https://cdn.example.com' : '',
}
```

### 11.1.4 SVG组件化方案

SVG在Next.js中有三种使用方式：

```tsx
// 方式1：作为图片引入（不能修改颜色）
import logo from '@/assets/logo.svg'
<Image src={logo} alt="Logo" />

// 方式2：作为React组件（推荐，可修改颜色/大小）
// 需要配置SVGR
// next.config.js
// module.exports = {
//   webpack(config) {
//     config.module.rules.push({
//       test: /\.svg$/,
//       use: ['@svgr/webpack'],
//     })
//     return config
//   },
// }
import Logo from '@/assets/logo.svg'
<Logo width={120} height={40} fill="currentColor" />

// 方式3：内联SVG（直接写SVG标签）
<svg width="24" height="24" viewBox="0 0 24 24">
  <path d="M12 2L2 22h20L12 2z" fill="currentColor" />
</svg>
```

### 11.1.5 静态资源版本管理与缓存策略

| 资源类型 | 缓存策略 | 过期时间 |
|---------|---------|---------|
| 带哈希的静态资源 | Cache-Control: immutable | 1年 |
| public/目录文件 | Cache-Control: public | 按需 |
| HTML文档 | Cache-Control: no-cache | 每次验证 |
| API响应 | Cache-Control: no-store | 不缓存 |

## 11.2 Image组件：图片自动优化、懒加载、自适应

### 11.2.1 next/image核心能力

next/image组件是Next.js最强大的内置优化工具：

```
原图 (2MB JPEG)
    ↓
next/image优化
    ↓
WebP/AVIF格式 (200-400KB)
    ↓
按设备尺寸resize (移动端更小)
    ↓
懒加载 + 模糊占位 + 渐进显示
```

| 优化能力 | 说明 | 默认开启 |
|---------|------|---------|
| 格式转换 | 自动转WebP/AVIF | 是 |
| 压缩 | 质量自适应 | 是 |
| Resize | 按设备尺寸生成响应式图片 | 是 |
| 懒加载 | 视口外图片延迟加载 | 是 |
| 模糊占位 | 加载前显示模糊缩略图 | 可选 |
| 防止CLS | 必须指定width/height | 是 |

### 11.2.2 Image组件必填属性

```tsx
import Image from 'next/image'

export default function Post({ cover }: { cover: string }) {
  return (
    <Image
      src={cover}
      width={800}
      height={600}
      alt="文章封面"
      // 可选属性
      priority={false}      // 首屏图片设为true
      placeholder="blur"    // 模糊占位
      quality={75}          // 压缩质量(1-100)
      loading="lazy"        // 懒加载(默认)
    />
  )
}
```

> width和height不是渲染尺寸，是宽高比。Next.js用这个比例在图片加载前预留空间，防止布局偏移(CLS)。不设这两个属性，你的Cumulative Layout Shift指标就废了。

### 11.2.3 fill属性：响应式图片布局

当你不知道图片尺寸时，用`fill`属性：

```tsx
export default function Hero() {
  return (
    <div style={{ position: 'relative', width: '100%', height: '400px' }}>
      <Image
        src="/images/hero.jpg"
        fill
        style={{ objectFit: 'cover' }}
        alt="Hero"
        priority
      />
    </div>
  )
}
```

fill属性要求父容器是`position: relative/absolute/fixed`，图片会填充父容器。

| object-fit值 | 效果 |
|-------------|------|
| cover | 填充容器，可能裁剪（最常用） |
| contain | 完整显示，可能留白 |
| fill | 拉伸填充（会变形） |

### 11.2.4 优先加载：priority属性与首屏图片

```tsx
// 首屏大图设priority，预加载
<Image src="/images/hero.jpg" fill priority alt="Hero" />

// 非首屏图片不设priority，懒加载
<Image src="/images/article-2.jpg" width={800} height={600} alt="文章2" />
```

priority做了两件事：
1. 添加`<link rel="preload">`预加载图片
2. 禁用懒加载，立即加载图片

> 不要给所有图片都加priority。priority意味着"抢带宽"，全抢等于没抢。只给首屏可见的1-2张大图加priority就够了。

### 11.2.5 图片格式自适应

Next.js自动根据浏览器支持情况返回最优格式：

```
浏览器支持AVIF → 返回AVIF (最小)
浏览器支持WebP → 返回WebP (较小)
都不支持 → 返回原图格式
```

```javascript
// next.config.js 配置格式和尺寸
const nextConfig = {
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    quality: 75,
  },
}
```

| 格式 | 压缩率 | 浏览器支持 | 推荐场景 |
|------|--------|-----------|---------|
| AVIF | 最高(比JPEG小50%) | 现代浏览器(90%+) | 默认首选 |
| WebP | 高(比JPEG小30%) | 绝大多数浏览器(95%+) | AVIF不支持时回退 |
| JPEG | 基准 | 所有 | 兼容旧浏览器 |
| PNG | 无损 | 所有 | 透明背景 |

## 11.3 远程图片配置与域名白名单

### 11.3.1 next.config.js中配置remotePatterns

```javascript
// next.config.js
const nextConfig = {
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'example.com' },
      { protocol: 'https', hostname: '**.example.com' }, // 通配符子域名
      { protocol: 'https', hostname: 'cdn.cloudflare.com', port: '', pathname: '/images/**' },
    ],
  },
}
```

### 11.3.2 域名白名单的安全意义

为什么必须配置白名单？因为next/image的优化接口可以代理任意图片URL。如果不限制域名，攻击者可以用你的服务器代理任意图片，消耗你的带宽和计算资源。

> 白名单不是限制，是防线。不设白名单的next/image相当于一个开放的图片代理服务，等着被薅。

### 11.3.3 动态图片代理：loader自定义

```javascript
// 自定义loader
import type { ImageLoaderProps } from 'next/image'

const cloudinaryLoader = ({ src, width, quality }: ImageLoaderProps) => {
  return `https://res.cloudinary.com/demo/image/fetch/w_${width},q_${quality || 75}/${src}`
}

// 使用
<Image src="photo.jpg" width={800} height={600} alt="Photo" loader={cloudinaryLoader} />
```

### 11.3.4 第三方图片服务集成

```javascript
// next.config.js - Cloudinary
const nextConfig = {
  images: {
    loader: 'cloudinary',
    path: 'https://res.cloudinary.com/my-account/image/fetch/',
  },
}

// next.config.js - Imgix
const nextConfig = {
  images: {
    loader: 'imgix',
    path: 'https://my-account.imgix.net/',
  },
}
```

### 11.3.5 远程图片优化性能与成本

| 优化方式 | 性能 | 成本 | 适用 |
|---------|------|------|------|
| Next.js内置优化 | 中 | 免费(自托管)或按量(Vercel) | 通用 |
| Cloudinary | 高 | 按量计费 | 大量图片 |
| Imgix | 高 | 按量计费 | CDN加速 |
| 构建时优化 | 最高 | 免费 | 图片已知且固定 |

## 11.4 字体优化：next/font零成本字体引入

### 11.4.1 next/font核心原理

```
传统方式：
浏览器下载HTML → 发现@font-face → 下载字体文件 → 渲染
问题：多次网络请求，FOIT/FOUT闪烁

next/font方式：
构建时下载字体 → 自托管在/_next/static/ → 零额外请求
```

> next/font的本质是"构建时自托管"。不是运行时优化，是把字体文件的下载从用户浏览器转移到了构建服务器。用户打开页面时字体已经在你的域名下了，零跨域请求。

### 11.4.2 Google Fonts接入

```tsx
// app/layout.tsx
import { Inter, Roboto } from 'next/font/google'

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  weight: ['400', '500', '700'],
  variable: '--font-inter',
})

const roboto = Roboto({
  subsets: ['latin'],
  display: 'swap',
  weight: ['400', '700'],
  variable: '--font-roboto',
})

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html className={`${inter.variable} ${roboto.variable}`}>
      <body>{children}</body>
    </html>
  )
}
```

### 11.4.3 本地字体接入

```tsx
import localFont from 'next/font/local'

const myFont = localFont({
  src: './fonts/MyCustomFont.woff2',
  display: 'swap',
  variable: '--font-my-custom',
})

// 支持多个字重
const multiWeightFont = localFont({
  src: [
    { path: './fonts/MyFont-Regular.woff2', weight: '400' },
    { path: './fonts/MyFont-Bold.woff2', weight: '700' },
  ],
  display: 'swap',
  variable: '--font-multi',
})
```

### 11.4.4 字体变量：CSS Variables跨组件共享

```css
/* 通过CSS变量使用字体 */
.title {
  font-family: var(--font-inter), sans-serif;
  font-weight: 700;
}

.body {
  font-family: var(--font-roboto), sans-serif;
  font-weight: 400;
}
```

### 11.4.5 字体加载策略

| font-display值 | 行为 | 体验 |
|---------------|------|------|
| swap | 先用回退字体，字体加载后替换 | FOUT（先看到文字） |
| block | 隐藏文字最多3秒，之后替换 | FOIT（先看到空白） |
| fallback | 100ms隐藏，3s超时 | 折中 |
| optional | 100ms隐藏，网络好才加载 | 最轻量 |

```tsx
// 推荐配置
const inter = Inter({
  subsets: ['latin'],
  display: 'swap', // FOUT，用户先看到文字，不空白
  preload: true,   // 预加载字体
})
```

> 字体加载最怕的不是慢，是空白。用户看到空白以为页面挂了，直接关掉。用display: 'swap'保证文字永远可见，哪怕先用回退字体渲染。

## 11.5 视频、音频媒体资源处理方案

### 11.5.1 视频自托管

```tsx
// public/videos/demo.mp4
export default function VideoBlock() {
  return (
    <video
      src="/videos/demo.mp4"
      controls
      preload="metadata"  // 只预加载元数据
      poster="/images/poster.jpg"  // 封面图
      width={1280}
      height={720}
    />
  )
}
```

大视频建议用流式加载（HLS/DASH），不要直接用mp4。

### 11.5.2 第三方视频嵌入

```tsx
// YouTube嵌入
export function YouTubeVideo({ videoId }: { videoId: string }) {
  return (
    <iframe
      src={`https://www.youtube.com/embed/${videoId}`}
      width="560"
      height="315"
      title="YouTube video"
      allowFullScreen
      loading="lazy"
    />
  )
}
```

### 11.5.3 音频资源处理

```tsx
export function AudioPlayer({ src }: { src: string }) {
  return (
    <audio src={src} controls preload="metadata">
      您的浏览器不支持音频播放。
    </audio>
  )
}
```

### 11.5.4 媒体文件的懒加载策略

```tsx
import { useState, useRef } from 'react'

export function LazyVideo({ src, poster }: { src: string; poster: string }) {
  const [loaded, setLoaded] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  // 用Intersection Observer懒加载
  // 视频进入视口才加载
  return (
    <div ref={ref} style={{ position: 'relative' }}>
      {!loaded && (
        <img src={poster} alt="视频封面" onClick={() => setLoaded(true)} />
      )}
      {loaded && (
        <video src={src} controls autoPlay width="100%" />
      )}
    </div>
  )
}
```

### 11.5.5 自定义视频播放器组件

```tsx
'use client'
import { useRef, useState } from 'react'

export function CustomVideoPlayer({ src }: { src: string }) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [playing, setPlaying] = useState(false)

  const togglePlay = () => {
    if (!videoRef.current) return
    if (playing) videoRef.current.pause()
    else videoRef.current.play()
    setPlaying(!playing)
  }

  return (
    <div className="video-player">
      <video ref={videoRef} src={src} onClick={togglePlay} />
      <button onClick={togglePlay}>{playing ? '暂停' : '播放'}</button>
    </div>
  )
}
```

## 11.6 资源打包优化与体积压缩

### 11.6.1 构建产物分析

```bash
# 安装bundle analyzer
npm install @next/bundle-analyzer

# next.config.js
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
})
module.exports = withBundleAnalyzer(nextConfig)

# 运行分析
ANALYZE=true npm run build
```

分析结果会打开两个页面：Server端和Client端的模块大小可视化。

### 11.6.2 Tree Shaking与按需引入

```tsx
// 错误：整包引入
import _ from 'lodash'
_.get(obj, 'a.b.c')

// 正确：按需引入
import get from 'lodash/get'
get(obj, 'a.b.c')

// 或者用支持Tree Shaking的替代库
import { get } from 'lodash-es'
```

> Tree Shaking不是自动的，它依赖你的import方式。整包import一个不支持Tree Shaking的库，打包工具只能把整个库都打进去。

### 11.6.3 大文件拆分与动态导入

```tsx
import dynamic from 'next/dynamic'

// 动态导入，按需加载
const HeavyChart = dynamic(() => import('@/components/HeavyChart'), {
  loading: () => <div>加载中...</div>,
  ssr: false,  // 只在客户端加载
})

export default function Dashboard() {
  return (
    <div>
      <h1>仪表盘</h1>
      <HeavyChart />
    </div>
  )
}
```

### 11.6.4 gzip与brotli压缩

| 压缩格式 | 压缩率 | 兼容性 | 推荐场景 |
|---------|--------|--------|---------|
| gzip | 中 | 所有 | 基础配置 |
| brotli | 高(比gzip小15-20%) | 现代浏览器 | 优先使用 |

```nginx
# Nginx配置brotli
brotli on;
brotli_comp_level 6;
brotli_types text/plain text/css application/json application/javascript;
```

Vercel等平台默认开启brotli压缩，无需额外配置。

### 11.6.5 打包体积监控与预警

| 监控维度 | 工具 | 预警阈值 |
|---------|------|---------|
| First Load JS | Next.js构建输出 | < 200KB |
| 总包体积 | bundle-analyzer | < 2MB |
| 单页面体积 | Lighthouse | < 500KB |
| 第三方库占比 | webpack-stats | < 30% |

> 包体积监控应该加到CI流水线里。每次PR自动检查First Load JS是否超标，超标直接拒绝合并。技术债不是一天积累的，是每次"就大一点点"积累的。

## 11.7 本章小结与课后练习

### 核心知识点回顾

| 知识点 | 关键内容 |
|--------|---------|
| 静态资源引入 | public直出 vs import构建优化 |
| Image组件 | 格式转换、resize、懒加载、防CLS |
| 远程图片 | remotePatterns白名单、自定义loader |
| next/font | 构建时自托管、零网络请求、display:swap |
| 媒体处理 | 视频/音频懒加载、第三方嵌入 |
| 打包优化 | bundle-analyzer、Tree Shaking、动态导入、压缩 |

### 课后练习

1. 用next/image替换项目中所有`<img>`标签，配置AVIF/WebP格式和模糊占位
2. 接入next/font，用Google Fonts替换CSS中的@font-face
3. 配置remotePatterns白名单，允许你的CDN域名图片通过next/image优化
4. 运行bundle-analyzer，找出最大的3个依赖并优化
5. 用dynamic导入实现一个组件的按需加载，测量First Load JS的变化

> 性能优化的精髓不是"用了什么高级技术"，而是"省了多少不必要的开销"。每减少1KB的First Load JS，用户就快一点看到页面。

觉得有用？收藏起来，下次优化资源加载直接照着做。

你的项目首屏加载要多久？评论区说说你的性能优化经验。

关注怕浪猫，下期我们讲Next.js的SEO（Search Engine Optimization，搜索引擎优化）与Metadata管理——从title/description到Open Graph，从sitemap到robots.txt，帮你让搜索引擎爱上你的网站。

**系列进度 11/16**

**怕浪猫说**

资源优化是那种"做了用户感受不到，不做用户骂娘"的工作。用户不会因为你的图片用了AVIF格式而夸你，但会因为首屏加载3秒而离开。这些细节加在一起，就是"专业"和"业余"的区别。下一章见。
