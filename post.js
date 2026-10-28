(() => {
    // 所有文章页启用选字批注（样式在 post.css）
    const annoScript = document.createElement('script');
    annoScript.src = 'annotate.js';
    annoScript.defer = true;
    document.head.append(annoScript);

    const loading = document.getElementById('loading');
    const errorContainer = document.getElementById('error-container');
    const errorMessage = document.getElementById('error-message');
    const contentContainer = document.getElementById('markdown-content');
    const retryButton = document.getElementById('retry-load');

    function showError(error) {
        loading.hidden = true;
        errorContainer.hidden = false;
        errorMessage.textContent = error.message;
    }

    function wrapCodeBlocks(html) {
        return html
            .replace(/<pre><code class="language-(.*?)">([\s\S]*?)<\/code><\/pre>/g, (_, lang, code) => `
<div class="code-block-wrapper">
  <div class="code-block-header">
    <span class="code-language">${lang}</span>
    <button type="button" class="copy-button code-copy-button">
      <i class="fas fa-copy" aria-hidden="true"></i> 复制代码
    </button>
  </div>
  <pre class="line-numbers language-${lang}"><code class="language-${lang}">${code}</code></pre>
</div>`)
            .replace(/<pre><code>([\s\S]*?)<\/code><\/pre>/g, (_, code) => `
<div class="code-block-wrapper">
  <div class="code-block-header">
    <span class="code-language">Text</span>
    <button type="button" class="copy-button code-copy-button">
      <i class="fas fa-copy" aria-hidden="true"></i> 复制代码
    </button>
  </div>
  <pre class="line-numbers"><code>${code}</code></pre>
</div>`);
    }

    async function loadMarkdown() {
        try {
            if (typeof marked === 'undefined' || typeof DOMPurify === 'undefined') {
                throw new Error('Markdown库加载失败');
            }

            const mdFile = document.body.dataset.markdown;
            if (!mdFile) {
                throw new Error('未配置Markdown文件');
            }

            loading.hidden = false;
            errorContainer.hidden = true;
            contentContainer.hidden = true;

            const response = await fetch(mdFile, { cache: 'no-store' });
            if (!response.ok) {
                throw new Error(`Markdown文件加载失败（HTTP ${response.status}）`);
            }

            const markdownText = await response.text();
            if (!markdownText.trim()) {
                throw new Error('Markdown文件为空');
            }

            const content = markdownText.replace(/^\uFEFF?---\s*\n([\s\S]*?)\n---\s*\n/, '');
            marked.setOptions({ breaks: true, gfm: true, smartypants: true });

            let html = marked.parse(content);
            html = html.replace(/<(\/?)h([1-5])(\s[^>]*)?>/g, (_, closing, level, attrs = '') =>
                `<${closing}h${Number(level) + 1}${attrs}>`
            );

            contentContainer.innerHTML = DOMPurify.sanitize(wrapCodeBlocks(html));
            contentContainer.hidden = false;
            loading.hidden = true;
            document.dispatchEvent(new CustomEvent('content:rendered'));

            if (typeof Prism !== 'undefined') {
                Prism.highlightAllUnder(contentContainer);
            }

            contentContainer.querySelectorAll('img').forEach(img => {
                img.loading = 'lazy';
                img.addEventListener('error', () => {
                    img.alt = '图片加载失败';
                }, { once: true });
            });
        } catch (error) {
            console.error(error);
            showError(error);
        }
    }

    async function copyCode(button) {
        const text = button.parentElement.nextElementSibling.textContent;
        let copied = false;
        try {
            if (!navigator.clipboard) {
                throw new Error('Clipboard API unavailable');
            }
            await navigator.clipboard.writeText(text);
            copied = true;
        } catch {
            const area = document.createElement('textarea');
            area.value = text;
            area.style.position = 'fixed';
            area.style.opacity = '0';
            document.body.append(area);
            area.select();
            copied = document.execCommand('copy');
            area.remove();
        }
        if (!copied) {
            button.textContent = '复制失败';
            return;
        }
        button.innerHTML = '<i class="fas fa-check" aria-hidden="true"></i> 已复制';
        button.classList.add('copied');
        setTimeout(() => {
            button.innerHTML = '<i class="fas fa-copy" aria-hidden="true"></i> 复制代码';
            button.classList.remove('copied');
        }, 2000);
    }

    retryButton.addEventListener('click', loadMarkdown);
    contentContainer.addEventListener('click', event => {
        const button = event.target.closest('.code-copy-button');
        if (button) {
            copyCode(button);
        }
    });

    window.reloadMarkdown = loadMarkdown;
    loadMarkdown();
})();

