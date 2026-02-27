import { marked, type Tokens } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

const baseUrl = import.meta.env.VITE_API_BASE_URL || ''

;(window as any).downloadImage = async (imageUrl: string, filename: string) => {
  try {
    const response = await fetch(imageUrl)
    const blob = await response.blob()
    const downloadUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = downloadUrl
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(downloadUrl)
  } catch (error) {
    console.error('Download failed:', error)
    window.open(imageUrl, '_blank')
  }
}

const renderer = new marked.Renderer()

renderer.code = ({ text, lang }: Tokens.Code): string => {
  let highlighted = text
  if (lang && hljs.getLanguage(lang)) {
    try {
      highlighted = hljs.highlight(text, { language: lang }).value
    } catch (err) {
      console.error(err)
    }
  } else {
    try {
      highlighted = hljs.highlightAuto(text).value
    } catch (err) {
      console.error(err)
    }
  }
  return `<pre><code class="hljs language-${lang || 'text'}">${highlighted}</code></pre>`
}

renderer.image = ({ href, title, text }: Tokens.Image): string => {
  let imageSrc = href
  if (imageSrc) {
    if (imageSrc.startsWith('/api/')) {
      imageSrc = `${baseUrl}${imageSrc}`
    } else if (!imageSrc.startsWith('http://') && !imageSrc.startsWith('https://') && !imageSrc.startsWith('data:')) {
      imageSrc = `${baseUrl}/api/v1/files/serve/${imageSrc}`
    }
  }
  const titleAttr = title ? ` title="${title}"` : ''
  return `<div class="image-container"><img src="${imageSrc}" alt="${text || ''}"${titleAttr} /><div class="image-overlay"><button class="download-btn" onclick="downloadImage('${imageSrc}', '${text || 'image'}.png')" title="下载图片"><svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg></button></div></div>`
}

renderer.link = ({ href, title, text }: Tokens.Link): string => {
  let linkHref = href
  if (linkHref) {
    if (linkHref.startsWith('/api/')) {
      linkHref = `${baseUrl}${linkHref}`
    } else if (!linkHref.startsWith('http://') && !linkHref.startsWith('https://')) {
      linkHref = `${baseUrl}/api/v1/files/serve/${linkHref}`
    }
  }
  const titleAttr = title ? ` title="${title}"` : ''
  const isDownload = href?.includes('download=true')
  const downloadAttr = isDownload ? ' download' : ''
  return `<a href="${linkHref}"${titleAttr} target="_blank" rel="noopener noreferrer"${downloadAttr}>${text}</a>`
}

marked.setOptions({
  renderer,
  breaks: true,
  gfm: true,
  async: false
})

const imageExtensions = /\.(png|jpe?g|gif|webp|bmp|svg|ico)(\?.*)?$/i

function processImageUrls(html: string): string {
  const imageUrlPattern = /(?<!["'=])(\/api\/v1\/files\/serve\/[^\s<>"']+)/g
  const fullUrlPattern = new RegExp(
    `(?<!["'=])(https?:\\/\\/[^\\s<>"']+${imageExtensions.source.slice(1)})`,
    'gi'
  )
  
  html = html.replace(imageUrlPattern, (match) => {
    if (imageExtensions.test(match)) {
      const fullUrl = `${baseUrl}${match}`
      return `<div class="image-container"><img src="${fullUrl}" alt="生成的图片" /><div class="image-overlay"><button class="download-btn" onclick="downloadImage('${fullUrl}', 'image.png')" title="下载图片"><svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg></button></div></div>`
    }
    return match
  })
  
  html = html.replace(fullUrlPattern, (match) => {
    return `<div class="image-container"><img src="${match}" alt="生成的图片" /><div class="image-overlay"><button class="download-btn" onclick="downloadImage('${match}', 'image.png')" title="下载图片"><svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg></button></div></div>`
  })
  
  return html
}

export const renderMarkdown = (content: string): string => {
  const html = marked.parse(content) as string
  return processImageUrls(html)
}