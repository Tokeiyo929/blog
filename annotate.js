// 文章页选字批注：选中正文文字 → 添加批注 → 高亮标记，点击标记查看/删除。
// 批注数据存 GitHub 私密 Gist（GIST_ID），跨浏览器/设备共享；localStorage 作本机缓存。
// token 不进仓库（GitHub 推送保护拦截，公开也会被自动吊销）：每台设备在文章页控制台执行一次
//   setAnnoCloud('ghp_你的gist权限token')
// token 只存该浏览器 localStorage，不配置则退回纯本机模式。
// 依赖 post.js 在内容渲染后派发 content:rendered 事件。
(() => {
    const STORE_KEY = 'blog-annotations';
    const CONTEXT = 24; // 定位用的前后文长度
    const GIST_ID = '70cd2d22d55555601e34ac21b157b05c'; // 私密 Gist，存 annotations.json
    const GIST_FILE = 'annotations.json';
    const CLOUD_KEY = 'blog-anno-cloud'; // 本机保存 { token }，不进仓库
    const content = document.getElementById('markdown-content');
    if (!content) return;

    // ---------- 存储 ----------
    // 按文件名而非完整路径做键：本地(127.0.0.1)与线上(/blog/)路径不同，文件名一致才能互通
    const articleKey = () => location.pathname.split('/').pop();
    const loadAll = () => {
        try { return JSON.parse(localStorage.getItem(STORE_KEY)) || {}; } catch { return {}; }
    };
    // 旧版按完整路径存，读取时迁移为按文件名
    const migrate = all => {
        const legacy = Object.keys(all).filter(k => k !== articleKey() && k.endsWith('/' + articleKey()));
        if (legacy.length) {
            all[articleKey()] = mergeLists([all[articleKey()], ...legacy.map(k => all[k])]);
            legacy.forEach(k => delete all[k]);
            localStorage.setItem(STORE_KEY, JSON.stringify(all));
        }
        return all;
    };
    const loadRaw = () => migrate(loadAll())[articleKey()] || []; // 含已删条目（墓碑），同步需携带
    const loadMine = () => loadRaw().filter(a => !a.deletedAt); // 界面只见未删除的
    const persistMine = list => {
        const all = loadAll();
        all[articleKey()] = list;
        localStorage.setItem(STORE_KEY, JSON.stringify(all));
        syncUp();
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
            // 头部截断后 target 已从 start 起，尾部切分须用相对 start 的偏移
            if (end - start < target.nodeValue.length) target.splitText(end - start);
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
    function openPop(getRect, build, mode) {
        closePop();
        pop = document.createElement('div');
        pop.className = 'anno-pop';
        build(pop);
        document.body.append(pop);
        pop._getRect = getRect;
        pop._mode = mode;
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
            // 真实点击“添加批注”时：click 先建好编辑器，本延迟回调随后执行且选区仍在，
            // 若不拦截会把编辑器抢换回气泡——即“弹窗一闪就消失”
            if (pop && pop._mode === 'editor') return;
            const sel = getSelection();
            if (!sel.rangeCount || sel.isCollapsed) {
                if (pop && pop._mode === 'bubble') closePop();
                return;
            }
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
            }, 'bubble');
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
        }, 'editor');
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
                // 就地打删除标记而非移除：墓碑随云同步传给其他设备，避免“删了又复活”
                persistMine(loadRaw().map(x => (x.id === a.id ? { ...x, deletedAt: Date.now() } : x)));
                content.querySelectorAll(`mark.text-anno[data-anno-id="${a.id}"]`).forEach(unwrap);
                closePop();
            });
            row.append(del);
            el.append(note, when, row);
        }, 'view');
    });

    // ---------- Gist 云同步 ----------
    const mergeLists = lists => {
        const byId = new Map();
        const ver = a => a.deletedAt || a.createdAt || 0; // 删除也是一次版本更新，新版本胜
        for (const list of lists) for (const a of list || []) {
            const cur = byId.get(a.id);
            if (!cur || ver(a) > ver(cur)) byId.set(a.id, a);
        }
        return [...byId.values()].sort((x, y) => (x.createdAt || 0) - (y.createdAt || 0));
    };
    const cloudReady = () => !!(GIST_ID && cloudConfig().token);
    const cloudConfig = () => {
        try { return JSON.parse(localStorage.getItem(CLOUD_KEY)) || {}; } catch { return {}; }
    };
    const gistHeaders = () => ({ Authorization: `Bearer ${cloudConfig().token}`, Accept: 'application/vnd.github+json' });
    const gistGet = () => fetch(`https://api.github.com/gists/${GIST_ID}`, { headers: gistHeaders() })
        .then(r => { if (!r.ok) throw new Error('gist get ' + r.status); return r.json(); })
        .then(g => JSON.parse((g.files && g.files[GIST_FILE] && g.files[GIST_FILE].content) || '{}'));
    const gistPut = data => fetch(`https://api.github.com/gists/${GIST_ID}`, {
        method: 'PATCH',
        headers: { ...gistHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ files: { [GIST_FILE]: { content: JSON.stringify(data, null, 2) } } })
    }).then(r => { if (!r.ok) throw new Error('gist put ' + r.status); });
    // 本地各文章的批注并入远端，远端没有的文章键原样保留
    const mergedWith = remote => {
        const local = loadAll();
        const merged = { ...remote };
        for (const k of Object.keys(local)) merged[k] = mergeLists([remote[k], local[k]]);
        return { merged, changed: JSON.stringify(merged) !== JSON.stringify(remote) };
    };
    let pushTimer = null;
    function syncUp() { // 增删改后合并写回 Gist，防抖避免连续操作狂刷 PATCH
        if (!cloudReady()) return;
        clearTimeout(pushTimer);
        pushTimer = setTimeout(() => {
            gistGet()
                .then(remote => { const { merged, changed } = mergedWith(remote); if (changed) return gistPut(merged); })
                .catch(err => console.warn('批注云同步失败，数据仍在本地', err));
        }, 800);
    }
    function syncDown() { // 打开页面：拉取 Gist 合并进 localStorage，远端批注才能渲染出高亮
        if (!cloudReady()) return;
        gistGet()
            .then(remote => {
                const { merged, changed } = mergedWith(remote);
                localStorage.setItem(STORE_KEY, JSON.stringify(merged));
                applyAll();
                if (changed) return gistPut(merged); // 本机多出的批注补传上去
            })
            .catch(err => console.warn('批注云拉取失败，先用本地数据', err));
    }

    // post.js 渲染完成（含重试）后恢复已有批注
    document.addEventListener('content:rendered', applyAll);
    syncDown();

    // 每台设备一次性配置（控制台执行，token 只存本机 localStorage）
    window.setAnnoCloud = token => {
        localStorage.setItem(CLOUD_KEY, JSON.stringify({ token }));
        location.reload();
    };
    window.clearAnnoCloud = () => {
        localStorage.removeItem(CLOUD_KEY);
        location.reload();
    };
})();
