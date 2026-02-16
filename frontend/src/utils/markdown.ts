import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

const renderer = new marked.Renderer()

renderer.code = (code: string, lang: string): string => {
  let highlighted = code
  if (lang && hljs.getLanguage(lang)) {
    try {
      highlighted = hljs.highlight(code, { language: lang }).value
    } catch (err) {
      console.error(err)
    }
  } else {
    try {
      highlighted = hljs.highlightAuto(code).value
    } catch (err) {
      console.error(err)
    }
  }
  return `<pre><code class="hljs language-${lang || 'text'}">${highlighted}</code></pre>`
}

marked.setOptions({
  renderer,
  breaks: true,
  gfm: true
})

export const renderMarkdown = (content: string): string => {
  return marked(content)
}