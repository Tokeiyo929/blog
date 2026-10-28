// 文章页选字批注：选中正文文字 → 添加批注 → 高亮标记，点击标记查看/删除。
// 批注存 localStorage（按文章路径区分），仅本机浏览器可见；依赖 post.js 在内容渲染后派发 content:rendered 事件。
(() => {
    const STORE_KEY = 'blog-annotations';
    const CONTEXT = 24; // 定位用的前后文长度
    const content = document.getElementById('markdown-content');
    if (!content) return;

    // ---------- 存储 ----------
    const articleKey = () => location.pathname;
    const loadAll = () => {
        try { return JSON.parse(localStorage.getItem(STORE_KEY)) || {}; } catch { return {}; }
    };
    const loadMine = () => loadAll()[articleKey()] || [];
    const persistMine = list => {
        const all = loadAll();
        all[articleKey()] = list;
        localStorage.setItem(STORE_KEY, JSON.stringify(all));
    };

    // ---------- 正文文本映射（DOM 文本节点 ⇄ 纯文本偏移） ----------
    function buildTextMap() {
        const walker = document.createTreeWalker(content, NodeFilter.SHOW_TEXT);
        const nodes = [];
        let full = '';
        let n;
        while ((n = walker.nextNode())) {
            nodes.push({ node: n, start: full.length });
            full += n.nodeValue;
        }
        return { nodes, full };
    }

    const allIndexOf = (full, text) => {
        const idxs = [];
        let i = 0;
        while (text && (i = full.indexOf(text, i)) !== -1) { idxs.push(i); i += 1; }
        return idxs;
    };

    // 优先按前后文定位，其次按出现次序
    function locate(map, a) {
        const idxs = allIndexOf(map.full, a.text);
        if (!idxs.length) return -1;
        const withCtx = idxs.filter(i =>
            (!a.prefix || map.full.slice(Math.max(0, i - a.prefix.length), i) === a.prefix) &&
            (!a.suffix || map.full.slice(i + a.text.length, i + a.text.length + a.suffix.length) === a.suffix));
        const list = withCtx.length ? withCtx : idxs;
        return list[Math.min(a.count || 0, list.length - 1)];
    }

    function offsetOf(map, node, offset) {
        if (node.nodeType !== Node.TEXT_NODE) return null;
        const entry = map.nodes.find(e => e.node === node);
        return entry ? entry.start + offset : null;
    }

    function wrapRange(map, start, end, id) {
        for (const { node, start: s } of map.nodes) {
            const e = s + node.nodeValue.length;
            if (e <= start || s >= end) continue;
            let target = node;
            if (start > s) target = target.splitText(start - s);
            if (end - s < target.nodeValue.length) target.splitText(end - s);
            if (!target.nodeValue) continue;
            const mark = document.createElement('mark');
            mark.className = 'text-anno';
            mark.dataset.annoId = id;
            mark.textContent = target.nodeValue;
            target.parentNode.replaceChild(mark, target);
        }
    }

    function unwrap(mark) {
        const parent = mark.parentNode;
        if (!parent) return;
        while (mark.firstChild) parent.insertBefore(mark.firstChild, mark);
        mark.remove();
        parent.normalize();
    }

    function applyAll() {
        content.querySelectorAll('mark.text-anno').forEach(unwrap);
        loadMine().forEach(a => {
            const map = buildTextMap();
            const idx = locate(map, a);
            if (idx >= 0) wrapRange(map, idx, idx + a.text.length, a.id);
        });
    }

    // ---------- 浮层 ----------
    let pop = null;
    function closePop() {
        if (pop) { pop.remove(); pop = null; }
    }
    // getRect() 返回锚点的当前视口坐标；返回 null 时保持原位
    function placePop(getRect) {
        const rect = getRect();
        if (!rect || (!rect.top && !rect.left && !rect.width && !rect.height)) return;
        const pad = 8;
        let x = rect.left;
        let y = rect.bottom + pad;
        if (y + pop.offsetHeight > window.innerHeight - pad) {
            y = Math.max(pad, rect.top - pop.offsetHeight - pad);
        }
        x = Math.max(pad, Math.min(x, window.innerWidth - pop.offsetWidth - pad));
        pop.style.left = `${x}px`;
        pop.style.top = `${y}px`;
    }
    function openPop(getRect, build) {
        closePop();
        pop = document.createElement('div');
        pop.className = 'anno-pop';
        build(pop);
        document.body.append(pop);
        pop._getRect = getRect;
        placePop(getRect);
    }
    // 弹层外按下才关闭；正文内的按下（含重新选字）不关，避免误闪
    document.addEventListener('mousedown', e => {
        if (pop && !pop.contains(e.target) && !content.contains(e.target)) closePop();
    });
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') closePop();
    });
    // 滚动跟随重新定位而不是关闭：触控板惯性滚动不会让弹窗闪消
    window.addEventListener('scroll', () => {
        if (pop && pop._getRect) placePop(pop._getRect);
    }, { passive: true });

    // ---------- 选字 → 添加批注 ----------
    let stash = null; // { map, start, end, rect }
    document.addEventListener('mouseup', () => {
        setTimeout(() => {
            const sel = getSelection();
            if (!sel.rangeCount || sel.isCollapsed) return;
            const range = sel.getRangeAt(0);
            if (!content.contains(range.commonAncestorContainer)) return;
            const map = buildTextMap();
            const startRaw = offsetOf(map, range.startContainer, range.startOffset);
            const endRaw = offsetOf(map, range.endContainer, range.endOffset);
            if (startRaw == null || endRaw == null || endRaw <= startRaw) return;
            const raw = map.full.slice(startRaw, endRaw);
            const lead = raw.length - raw.trimStart().length;
            const trail = raw.length - raw.trimEnd().length;
            const start = startRaw + lead;
            const end = endRaw - trail;
            if (end <= start) return;
            stash = { map, start, end, range: range.cloneRange() };
            openPop(() => (stash && stash.range ? stash.range.getBoundingClientRect() : null), el => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'anno-bubble';
                btn.textContent = '添加批注';
                btn.addEventListener('click', showEditor);
                el.append(btn);
            });
        }, 0);
    });

    function showEditor() {
        if (!stash) return;
        openPop(() => (stash && stash.range ? stash.range.getBoundingClientRect() : null), el => {
            const ta = document.createElement('textarea');
            ta.className = 'anno-input';
            ta.placeholder = '输入批注内容…';
            const row = document.createElement('div');
            row.className = 'anno-actions';
            const save = document.createElement('button');
            save.type = 'button';
            save.className = 'anno-save';
            save.textContent = '保存';
            const cancel = document.createElement('button');
            cancel.type = 'button';
            cancel.className = 'anno-cancel';
            cancel.textContent = '取消';
            cancel.addEventListener('click', closePop);
            save.addEventListener('click', saveAnno);
            ta.addEventListener('keydown', e => {
                if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                    e.preventDefault();
                    saveAnno();
                }
            });
            row.append(save, cancel);
            el.append(ta, row);
            ta.focus({ preventScroll: true });
        });
    }

    function saveAnno() {
        if (!stash || !pop) return;
        const note = pop.querySelector('.anno-input').value.trim();
        if (!note) return;
        const { map, start, end } = stash;
        const text = map.full.slice(start, end);
        const a = {
            id: 'a' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
            note,
            text,
            prefix: map.full.slice(Math.max(0, start - CONTEXT), start),
            suffix: map.full.slice(end, end + CONTEXT),
            count: allIndexOf(map.full, text).indexOf(start),
            createdAt: Date.now()
        };
        const list = loadMine();
        list.push(a);
        persistMine(list);
        wrapRange(buildTextMap(), start, end, a.id);
        stash = null;
        closePop();
        getSelection().removeAllRanges();
    }

    // ---------- 点击标记 → 查看/删除 ----------
    content.addEventListener('click', e => {
        const mark = e.target.closest('mark.text-anno');
        if (!mark) return;
        const a = loadMine().find(x => x.id === mark.dataset.annoId);
        if (!a) return;
        openPop(() => (mark.isConnected ? mark.getBoundingClientRect() : null), el => {
            const note = document.createElement('div');
            note.className = 'anno-note';
            note.textContent = a.note;
            const when = document.createElement('div');
            when.className = 'anno-date';
            when.textContent = new Date(a.createdAt).toLocaleString();
            const row = document.createElement('div');
            row.className = 'anno-actions';
            const del = document.createElement('button');
            del.type = 'button';
            del.className = 'anno-del';
            del.textContent = '删除';
            del.addEventListener('click', () => {
                persistMine(loadMine().filter(x => x.id !== a.id));
                content.querySelectorAll(`mark.text-anno[data-anno-id="${a.id}"]`).forEach(unwrap);
                closePop();
            });
            row.append(del);
            el.append(note, when, row);
        });
    });

    // post.js 渲染完成（含重试）后恢复已有批注
    document.addEventListener('content:rendered', applyAll);
})();
