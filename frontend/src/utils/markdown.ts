import { marked, type Tokens } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

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

marked.setOptions({
  renderer,
  breaks: true,
  gfm: true,
  async: false
})

export const renderMarkdown = (content: string): string => {
  return marked.parse(content) as string
}