"""
Sieve — slice and dice spreadsheets: dark glass-morphism UI, FastHTML + HTMX, pandas.
Upload → filter → browse → inspect → export.
"""

from pathlib import Path
from io import BytesIO

import json
import re
import time
from urllib.parse import quote

import pandas as pd
from fasthtml.common import (
    FastHTML, Style, Script, File, StaticFiles, Request,
    A, Button, Details, Div, Form, H2, H4, Input,
    Label, Option, P, Select, Span, Summary, Svg,
)
from pathlib import Path  # used for upload filename suffix only
from fasthtml.svg import Circle, Path as SvgPath  # NOT fasthtml.common.Path — that's pathlib.Path!

# ═══════════════════════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════════════════════

CSS = r"""
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
/* Four palettes, two design languages. "Ink" (dark, the CSS default) and
   "Paper" (light) share flat panels, hairline rules, antique-brass accent,
   serif headings with mono numerals. "Frost" (Apple light) and "Midnight"
   (true-black Apple dark) use SF Pro stacks, larger radii, blue accent.
   Selected via [data-theme="…"] on <html> (see HEAD_JS). Every surface color
   is a token — a theme is just a var block. */
:root{
  --bg:#131519;--bg2:#181b21;--bg3:#101217;
  --panel:#1b1e24;--panel2:#22262e;
  --accent:#c9a45c;--accent2:#b8934a;--accent-ink:#17191e;
  --glow:rgba(201,164,92,.14);--glow2:rgba(201,164,92,.35);
  --border:rgba(233,229,220,.13);--border2:rgba(233,229,220,.26);
  --hairline:rgba(233,229,220,.06);--hover:rgba(233,229,220,.05);--hover2:rgba(233,229,220,.09);
  --field:rgba(0,0,0,.25);--cell:rgba(0,0,0,.2);--dz-bg:rgba(0,0,0,.18);
  --txt:#d8d4ca;--txt2:#f0ece2;--dim:#9a958a;--muted:#6e6a62;
  --danger:#e05260;--success:#5cb87f;
  --overlay:rgba(19,21,25,.78);
  --panel-shadow:0 1px 3px rgba(0,0,0,.35),0 8px 28px rgba(0,0,0,.3);
  --r:6px;--rs:4px;
  --font-ui:'Helvetica Neue',Helvetica,'Segoe UI Variable Text','Segoe UI',system-ui,Arial,sans-serif;
  --font-serif:'Iowan Old Style','Palatino Linotype',Palatino,Georgia,'Times New Roman',serif;
  --font-mono:'SF Mono','Cascadia Mono',Consolas,'Liberation Mono',Menlo,monospace;
}
[data-theme="light"]{
  --bg:#f2efe8;--bg2:#eae6dc;--bg3:#f8f6f1;
  --panel:#fbfaf6;--panel2:#f1eee5;
  --accent:#8a6a1f;--accent2:#6f5518;--accent-ink:#fdfcf8;
  --glow:rgba(138,106,31,.12);--glow2:rgba(138,106,31,.3);
  --border:rgba(28,30,34,.18);--border2:rgba(28,30,34,.38);
  --hairline:rgba(28,30,34,.08);--hover:rgba(28,30,34,.045);--hover2:rgba(28,30,34,.07);
  --field:#ffffff;--cell:#f5f2ea;--dz-bg:#fbfaf6;
  --txt:#33363c;--txt2:#1c1e22;--dim:#6a6d74;--muted:#8b8e95;
  --danger:#c02f3e;--success:#1e8a4c;
  --overlay:rgba(242,239,232,.82);
  --panel-shadow:0 1px 2px rgba(60,50,30,.08),0 6px 24px rgba(60,50,30,.1);
}
[data-theme="frost"]{
  --bg:#f5f5f7;--bg2:#ebebed;--bg3:#fbfbfd;
  --panel:#ffffff;--panel2:#f5f5f7;
  --accent:#0071e3;--accent2:#0077ed;--accent-ink:#ffffff;
  --glow:rgba(0,113,227,.1);--glow2:rgba(0,113,227,.25);
  --border:rgba(0,0,0,.12);--border2:rgba(0,0,0,.25);
  --hairline:rgba(0,0,0,.06);--hover:rgba(0,0,0,.04);--hover2:rgba(0,0,0,.06);
  --field:#ffffff;--cell:#f5f5f7;--dz-bg:#fbfbfd;
  --txt:#33333a;--txt2:#1d1d1f;--dim:#6e6e73;--muted:#86868b;
  --danger:#d70015;--success:#248a3d;
  --overlay:rgba(245,245,247,.8);
  --panel-shadow:0 1px 2px rgba(0,0,0,.06),0 8px 24px rgba(0,0,0,.08);
  --r:12px;--rs:8px;
  --font-ui:-apple-system,BlinkMacSystemFont,'SF Pro Text','Inter','Helvetica Neue',system-ui,sans-serif;
  --font-serif:-apple-system,BlinkMacSystemFont,'SF Pro Display','Inter','Helvetica Neue',system-ui,sans-serif;
}
[data-theme="midnight"]{
  --bg:#000000;--bg2:#0b0b0d;--bg3:#000000;
  --panel:#1c1c1e;--panel2:#2c2c2e;
  --accent:#0a84ff;--accent2:#409cff;--accent-ink:#ffffff;
  --glow:rgba(10,132,255,.14);--glow2:rgba(10,132,255,.3);
  --border:rgba(255,255,255,.14);--border2:rgba(255,255,255,.28);
  --hairline:rgba(255,255,255,.07);--hover:rgba(255,255,255,.05);--hover2:rgba(255,255,255,.08);
  --field:rgba(255,255,255,.08);--cell:rgba(255,255,255,.04);--dz-bg:rgba(255,255,255,.05);
  --txt:#d1d1d6;--txt2:#f5f5f7;--dim:#98989d;--muted:#6c6c72;
  --danger:#ff453a;--success:#30d158;
  --overlay:rgba(0,0,0,.72);
  --panel-shadow:0 1px 3px rgba(0,0,0,.5),0 8px 28px rgba(0,0,0,.45);
  --r:12px;--rs:8px;
  --font-ui:-apple-system,BlinkMacSystemFont,'SF Pro Text','Inter','Helvetica Neue',system-ui,sans-serif;
  --font-serif:-apple-system,BlinkMacSystemFont,'SF Pro Display','Inter','Helvetica Neue',system-ui,sans-serif;
}
html,body{height:100%;width:100%;font-family:var(--font-ui);
  background:var(--bg);color:var(--txt);font-size:13.5px;line-height:1.5;
  font-variant-numeric:tabular-nums;-webkit-font-smoothing:antialiased}

/* Layout */
.app{display:flex;height:100vh;padding:0 10px}
.pnl{display:flex;flex-direction:column;overflow:hidden;background:var(--panel);
  border:1px solid var(--border);border-radius:var(--r);box-shadow:var(--panel-shadow);
  min-width:180px}
.rh{width:6px;flex-shrink:0;cursor:col-resize;display:flex;align-items:center;justify-content:center;
  transition:background .15s}
.rh:hover,.rh.drag{background:var(--accent)}
.rh::after{content:"";width:2px;height:24px;border-radius:1px;background:var(--border)}
.rh:hover::after,.rh.drag::after{background:var(--accent)}

/* Resize handles */
.rsz{width:6px;cursor:col-resize;display:flex;align-items:center;justify-content:center;
  flex-shrink:0;transition:background .15s}
.rsz:hover,.rsz.on{background:var(--accent)}
.rsz-i{width:2px;height:32px;border-radius:1px;background:var(--border2);transition:background .15s}
.rsz:hover .rsz-i,.rsz.on .rsz-i{background:var(--accent);height:48px}
.pnh{padding:14px 16px;border-bottom:1px solid var(--border);flex-shrink:0;position:relative}
.pnb{flex:1;overflow-y:auto;padding:12px}
.pnb::-webkit-scrollbar{width:5px}
.pnb::-webkit-scrollbar-track{background:0 0}
.pnb::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
.pnb::-webkit-scrollbar-thumb:hover{background:var(--border2)}

/* Sidebar */
.stitle{font-family:var(--font-serif);font-size:17px;font-weight:600;
  color:var(--txt2);letter-spacing:.01em}
.stitle::after{content:"";display:block;width:26px;height:2px;
  background:var(--accent);margin-top:5px;border-radius:1px}
.ssub{font-family:var(--font-mono);font-size:10px;color:var(--muted);margin-top:4px}
.theme-btn{position:absolute;top:12px;right:12px;padding:3px 9px;
  border:1px solid var(--border);border-radius:var(--rs);background:transparent;
  color:var(--dim);font-family:var(--font-ui);font-size:10px;letter-spacing:.04em;
  cursor:pointer;transition:all .15s}
.theme-btn:hover,.theme-btn:focus-visible{border-color:var(--accent);color:var(--txt2)}
.tpop{position:absolute;top:38px;right:10px;z-index:60;display:none;min-width:168px;
  background:var(--panel);border:1px solid var(--border);border-radius:var(--r);
  box-shadow:var(--panel-shadow);padding:4px}
.tpop.open{display:block}
.tpop-h{font-size:10px;text-transform:uppercase;letter-spacing:.08em;
  color:var(--muted);padding:6px 10px 4px}
.topt{display:flex;align-items:center;gap:8px;padding:7px 10px;border-radius:var(--rs);
  cursor:pointer;font-size:12px;color:var(--txt)}
.topt:hover{background:var(--hover)}
.topt.on{color:var(--txt2)}
.tsw{width:14px;height:14px;border-radius:50%;border:1px solid var(--border2);flex-shrink:0}
.tck{margin-left:auto;visibility:hidden;color:var(--accent);font-weight:600}
.topt.on .tck{visibility:visible}
.sect{margin-bottom:14px}
.slbl{display:block;font-size:10px;font-weight:600;text-transform:uppercase;
  letter-spacing:.09em;color:var(--muted);margin-bottom:5px}

/* Upload */
.dz{border:1px dashed var(--border2);border-radius:var(--r);padding:20px 12px;
  text-align:center;cursor:pointer;transition:all .2s;background:var(--dz-bg)}
.dz:hover,.dz.on{border-color:var(--accent);background:var(--glow)}
.dz-i{font-size:32px;display:block;margin-bottom:4px}
.dz-t{font-size:12px;color:var(--dim)}
.dz-f{font-size:11px;color:var(--accent);margin-top:6px;word-break:break-all}

/* Buttons */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:5px;
  padding:7px 12px;border:1px solid var(--border);border-radius:var(--rs);
  background:var(--glass2);color:var(--txt);font-size:12px;font-weight:500;
  cursor:pointer;transition:all .15s;text-decoration:none;font-family:inherit}
.btn:hover{background:var(--hover2);border-color:var(--border2)}
.bp{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
.bp:hover{background:var(--accent2);border-color:var(--accent2)}
.bxs{padding:2px 8px;font-size:10px}
.bc{border-color:var(--border);color:var(--danger)}
.bc:hover{background:var(--hover2);border-color:var(--danger)}

/* Inputs */
input[type="text"],input[type="search"],select{width:100%;padding:7px 10px;
  border:1px solid var(--border);border-radius:var(--rs);
  background:var(--field);color:var(--txt);font-size:12px;
  font-family:inherit;outline:none;transition:border-color .15s,box-shadow .15s}
input:focus,select:focus{border-color:var(--accent);box-shadow:0 0 0 2px var(--glow)}
select{cursor:pointer}
select option{background:var(--panel);color:var(--txt)}

/* Sheet tabs */
.stabs{display:flex;flex-wrap:wrap;gap:3px}
.stab{padding:5px 10px;border-radius:var(--rs);border:1px solid var(--border);
  background:0 0;color:var(--dim);font-size:11px;font-family:inherit;cursor:pointer;transition:all .15s}
.stab:hover{border-color:var(--accent);color:var(--txt)}
.stab.on{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}

/* Row cards */
.rcard{padding:10px 12px;border-radius:var(--rs);border:1px solid transparent;
  cursor:pointer;transition:all .12s;margin-bottom:3px}
.rcard:hover{background:var(--hover);border-color:var(--border)}
.rcard.sel{background:var(--glow);border-color:var(--accent)}
.rcard:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
.rcard{content-visibility:auto;contain-intrinsic-size:auto 64px}
.rtitle{font-family:var(--font-serif);font-size:14px;font-weight:600;color:var(--txt2);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rsub{font-size:11px;color:var(--dim);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ridx{font-family:var(--font-mono);font-size:9px;color:var(--muted);margin-top:1px}

/* Detail grid */
.dgrid{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.dcell{padding:8px 10px;border-radius:var(--rs);background:var(--cell);
  border:1px solid var(--border)}
.dcell .lbl{font-size:9px;font-weight:600;text-transform:uppercase;
  letter-spacing:.09em;color:var(--muted);margin-bottom:3px}
.dcell .val{font-family:var(--font-mono);font-size:11.5px;word-break:break-word;
  color:var(--txt2);line-height:1.5}
.dcell .val:empty::before{content:"\2014";color:var(--muted)}
.dhead{display:flex;align-items:center;justify-content:space-between;gap:6px}
.copy-btn{padding:1px 5px;border:1px solid var(--border);border-radius:3px;
  background:transparent;color:var(--dim);font:inherit;font-size:9px;cursor:pointer}
.copy-btn:hover,.copy-btn:focus-visible{border-color:var(--accent);color:var(--txt)}

/* Chips */
.fgrp{margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid var(--hairline);
  content-visibility:auto;contain-intrinsic-size:auto 42px}
.fgrp summary{list-style:none;cursor:pointer;display:flex;align-items:center;
  justify-content:space-between;gap:6px}
.fgrp summary::-webkit-details-marker{display:none}
.fgrp summary:hover .fgrp-t{color:var(--txt2)}
.fgrp-on{color:var(--accent);font-size:10px;font-weight:600;white-space:nowrap}
.fgrp-body{padding-top:6px}
.fgrp-t{font-size:10.5px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;
  color:var(--dim);margin-bottom:4px}
/* Chip scroll boxes (Detail/Filter Columns pickers, filter groups).
   .tall (many chips) gets a roomier default height and a JS drag handle
   (.fchips-h, see resize grip JS) — native resize grips are too fiddly. */
.fchips{display:flex;flex-wrap:wrap;gap:3px;overflow-y:auto;max-height:60vh}
.fchips.tall{height:180px;min-height:48px}
.fchips-h{height:10px;margin:2px 0 4px;cursor:row-resize;display:flex;
  align-items:center;justify-content:center;flex-shrink:0;border-radius:3px}
.fchips-h::after{content:"";width:28px;height:3px;border-radius:2px;background:var(--border2)}
.fchips-h:hover::after,.fchips-h.drag::after{background:var(--accent)}
.chip{display:inline-flex;align-items:center;gap:2px;padding:2px 7px;
  border-radius:3px;border:1px solid var(--border);font-family:var(--font-mono);font-size:10px;
  cursor:pointer;transition:all .12s;background:0 0;color:var(--dim);user-select:none}
.chip:hover{border-color:var(--accent);color:var(--txt)}
.chip.on{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
.chip input{display:none}
.colf-more{font-size:10px;color:var(--muted);padding:4px 2px 2px;
  align-items:center;gap:6px;flex-wrap:wrap;display:none}
.colf-more.on{display:flex}
.cf-hide{display:none!important}

/* Result bar */
.rbar{display:flex;align-items:center;justify-content:space-between;
  font-family:var(--font-mono);font-size:10px;color:var(--muted);padding:6px 14px;
  border-bottom:1px solid var(--hairline);flex-shrink:0}
.rbar span{display:flex;align-items:center;gap:4px}

/* Welcome/empty */
.welcome{display:flex;flex-direction:column;align-items:center;justify-content:center;
  height:100%;text-align:center;color:var(--dim)}
.welcome .ic{font-size:48px;margin-bottom:12px;opacity:.85}
.welcome h2{font-family:var(--font-serif);font-size:18px;font-weight:600;color:var(--txt2);margin-bottom:6px}
.welcome p{font-size:12px;max-width:260px;line-height:1.6}
.empty{text-align:center;padding:24px;color:var(--muted);font-size:12px}

/* Animations */
@keyframes fadeIn{from{opacity:0;transform:translateY(-2px)}to{opacity:1;transform:none}}
@keyframes spin{to{transform:rotate(360deg)}}
.htmx-added{animation:fadeIn .15s ease}

/* Loading indicator */
.loading-overlay{
  position:fixed;top:0;left:0;right:0;bottom:0;
  background:var(--overlay);backdrop-filter:blur(4px);
  display:flex;align-items:center;justify-content:center;
  z-index:9999;opacity:0;transition:opacity 0.2s;pointer-events:none;
}
.loading-overlay.active{opacity:1;pointer-events:auto}
.loading-spinner{
  width:40px;height:40px;border:3px solid var(--border);
  border-top-color:var(--accent);border-radius:50%;
  animation:spin 0.8s linear infinite;
}

/* Util */
.mt4{margin-top:4px}.mt6{margin-top:6px}.mb4{margin-bottom:4px}
.wf{width:100%}.flex{display:flex}.g2{gap:2px}.g4{gap:4px}
.hidden{display:none!important}
"""

# ═══════════════════════════════════════════════════════════════════════════
# JavaScript
# ═══════════════════════════════════════════════════════════════════════════

JS = r"""
document.addEventListener('DOMContentLoaded', () => {
  // Drag-and-drop. All handlers are DELEGATED to document: upload, sheet
  // switches, and close replace #app via outerHTML, which destroys the
  // dropzone element. Direct listeners would silently die with it.
  const dropForm = () => document.getElementById('upload-form');
  const inDropzone = ev => ev.target?.closest?.('#dropzone');
  ['dragenter','dragover'].forEach(e => document.addEventListener(e, ev => {
    const dz = inDropzone(ev); if (!dz) return;
    ev.preventDefault(); dz.classList.add('on');
  }));
  ['dragleave','drop'].forEach(e => document.addEventListener(e, ev => {
    const dz = inDropzone(ev); if (!dz) return;
    ev.preventDefault(); dz.classList.remove('on');
  }));
  document.addEventListener('drop', ev => {
    if (!inDropzone(ev)) return;
    const form = dropForm();
    if (ev.dataTransfer.files.length && form) {
      form.querySelector('input[type="file"]').files = ev.dataTransfer.files;
      form.requestSubmit();
    }
  });
  document.addEventListener('click', ev => {
    if (!inDropzone(ev)) return;
    dropForm()?.querySelector('input[type="file"]')?.click();
  });

  // Row selection highlighting
  document.addEventListener('click', ev => {
    const card = ev.target.closest('.rcard');
    if (!card) return;
    document.querySelectorAll('.rcard.sel').forEach(c => c.classList.remove('sel'));
    card.classList.add('sel');
  });

  // Keep chip styling in sync with native checkbox changes. Filter groups
  // opt into auto-submit; detail columns are committed with Apply.
  document.addEventListener('change', ev => {
    const cb = ev.target.closest('.chip input[type="checkbox"]');
    if (!cb) return;
    const chip = cb.closest('.chip');
    chip?.classList.toggle('on', cb.checked);
    if (cb.form?.dataset.autosubmit === 'true') cb.form.requestSubmit();
  });

  // Select-all / Clear-all
  document.addEventListener('click', ev => {
    const btn = ev.target.closest('[data-sel], [data-clear]');
    if (!btn) return;
    const group = btn.closest('.fgrp, .sect');
    if (!group) return;
    const all = btn.hasAttribute('data-sel');
    group.querySelectorAll('.chip').forEach(c => {
      const cb = c.querySelector('input[type="checkbox"]');
      if (cb) { cb.checked = all; c.classList.toggle('on', all); }
    });
    const form = group.matches('form') ? group : group.querySelector('form');
    // Detail columns commit explicitly via Apply; their All/Clear buttons are
    // pure client-side bulk toggles and must not auto-submit.
    if (form && !form.closest('#detail-pick, #filter-pick')) form.requestSubmit();
  });

  // ── Filter chip search + filter-group cap ─────────────────────────
  // #fc-search narrows the Filter Columns picker chips client-side.
  // The group list shows at most CF_CAP stubs (plus stubs with an active
  // filter, which always stay visible); capping is pure client-side.
  const CF_CAP = 30, CF_STEP = 50;
  let cfShown = CF_CAP;
  const applyColFilterView = () => {
    const list = document.getElementById('col-filters');
    const foot = document.getElementById('colf-more');
    if (!list || !foot) return;
    const stubs = [...list.querySelectorAll('.fgrp')];
    const isActive = el => !!el.querySelector('.fgrp-on');
    let rest = 0;
    stubs.forEach(el => {
      let vis;
      if (isActive(el)) vis = true;
      else { rest += 1; vis = rest <= cfShown; }
      // Class-based (not inline style): htmx 2's settle pass re-clones
      // style attributes from stale nodes after afterSwap, which clobbers
      // any JS-set inline display. !important + afterSettle survives it.
      el.classList.toggle('cf-hide', !vis);
    });
    const total = stubs.length;
    const shown = stubs.filter(el => !el.classList.contains('cf-hide')).length;
    foot.innerHTML = '';
    foot.classList.toggle('on', shown < total);
    if (shown >= total) return;
    foot.append(`Showing ${shown} of ${total} — `);
    const b = document.createElement('button');
    b.className = 'btn bxs'; b.type = 'button';
    b.dataset.cfmore = '';
    b.textContent = 'show more';
    foot.append(b);
  };
  document.addEventListener('input', ev => {
    if (ev.target?.id !== 'fc-search') return;
    const q = ev.target.value.trim().toLowerCase();
    document.querySelectorAll('#fc-chips .chip').forEach(ch =>
      ch.classList.toggle('cf-hide', !!q && !ch.textContent.toLowerCase().includes(q)));
  });
  document.addEventListener('click', ev => {
    if (!ev.target?.closest?.('[data-cfmore]')) return;
    cfShown += CF_STEP;
    applyColFilterView();
  });
  // Re-apply after swaps (stubs may have been rebuilt). afterSettle is the
  // one that actually sticks: it fires after htmx finishes cloning/attr
  // fixups that would otherwise overwrite our visibility classes.
  const cfReswap = ev => {
    const id = ev.detail.target?.id;
    if (id === 'app' || id === 'col-filters') cfShown = CF_CAP;
    applyColFilterView();
  };
  document.body.addEventListener('htmx:afterSwap', cfReswap);
  document.body.addEventListener('htmx:afterSettle', cfReswap);
  applyColFilterView();

  // The loaded-state Change control opens the existing hidden file input.
  document.addEventListener('click', ev => {
    const opener = ev.target.closest('[data-open-file]');
    if (!opener) return;
    opener.closest('form')?.querySelector('input[type="file"]')?.click();
  });
  document.addEventListener('change', ev => {
    if (ev.target.matches('#fi') && ev.target.files.length) ev.target.form?.requestSubmit();
  });

  // Theme picker — state lives on <html> (see HEAD_JS), persisted in
  // localStorage; popover opens from the gear button. All handlers are
  // delegated so they survive full #app swaps. Open/close is class-based
  // (htmx re-clones inline styles after swaps).
  const closePop = () => { const p = document.getElementById('theme-pop'); if (p) p.classList.remove('open'); };
  const syncThemeOpts = () => {
    const t = document.documentElement.dataset.theme;
    document.querySelectorAll('[data-theme-opt]').forEach(o => o.classList.toggle('on', o.dataset.themeOpt === t));
  };
  function setTheme(t) {
    document.documentElement.dataset.theme = t;
    try { localStorage.setItem('xv-theme', t); } catch (_) {}
    syncThemeOpts();
  }
  document.addEventListener('click', ev => {
    if (ev.target.closest('#settings-btn')) {
      const p = document.getElementById('theme-pop');
      if (p) { const was = p.classList.contains('open'); closePop(); syncThemeOpts(); if (!was) p.classList.add('open'); }
      return;
    }
    const o = ev.target.closest('[data-theme-opt]');
    if (o) { setTheme(o.dataset.themeOpt); closePop(); return; }
    if (!ev.target.closest('#theme-pop')) closePop();
  });
  document.addEventListener('keydown', ev => { if (ev.key === 'Escape') closePop(); });
  document.body.addEventListener('htmx:afterSwap', syncThemeOpts);
  syncThemeOpts();

  // Row cards behave like a small keyboard-navigable list.
  document.addEventListener('keydown', ev => {
    const card = ev.target.closest('.rcard');
    if (!card) return;
    if (ev.key === 'Enter' || ev.key === ' ') {
      ev.preventDefault();
      card.click();
      return;
    }
    if (ev.key !== 'ArrowUp' && ev.key !== 'ArrowDown') return;
    const cards = [...document.querySelectorAll('#main-wrap .rcard')];
    const current = cards.indexOf(card);
    const next = current + (ev.key === 'ArrowDown' ? 1 : -1);
    if (next >= 0 && next < cards.length) {
      ev.preventDefault();
      cards[next].focus();
    }
  });

  // Detail swaps should always start at the top of the pane.
  document.body.addEventListener('htmx:afterSwap', ev => {
    if (ev.detail.target?.id === 'detail') ev.detail.target.scrollTop = 0;
  });

  // Keep copying a value a deliberate, keyboard-accessible action.
  document.addEventListener('click', async ev => {
    const btn = ev.target.closest('[data-copy-value]');
    if (!btn) return;
    ev.preventDefault();
    ev.stopPropagation();
    try {
      await navigator.clipboard.writeText(btn.dataset.copyValue || '');
      const original = btn.textContent;
      btn.textContent = 'Copied';
      setTimeout(() => { btn.textContent = original; }, 900);
    } catch (_) {
      btn.textContent = 'Copy failed';
    }
  });

  // Loading indicator
  const overlay = document.createElement('div');
  overlay.className = 'loading-overlay';
  overlay.innerHTML = '<div class="loading-spinner"></div>';
  document.body.appendChild(overlay);
  
  // Only heavyweight requests (upload, sheet switch, close) deserve a modal
  // overlay; debounced search/filter requests would make it strobe and block
  // typing.
  const isHeavy = elt => !!elt?.closest?.('#upload-form, .stabs, [hx-post="/close"]');
  // The afterRequest cleanup must hang off the REQUESTING ELEMENT, not body:
  // these requests outerHTML-swap #app, so by the time htmx fires afterRequest
  // the element is detached and its event never bubbles to document. A
  // body-level listener misses it and the click-blocking overlay sticks
  // forever — the classic "app became non-responsive after upload" freeze.
  document.body.addEventListener('htmx:beforeRequest', ev => {
    const elt = ev.detail.elt;
    if (!isHeavy(elt)) return;
    overlay.classList.add('active');
    elt.addEventListener('htmx:afterRequest',
      () => overlay.classList.remove('active'), { once: true });
  });

  // ── Panel resize ─────────────────────────────────────────────────────
  // Delegated like everything else, and panels are looked up FRESH at drag
  // time — full #app swaps replace them, so cached references go stale.
  let drag = null;
  const panels = () => ({
    left: document.getElementById('pnl-left'),
    mid: document.getElementById('pnl-mid'),
    right: document.getElementById('pnl-right'),
  });

  document.addEventListener('mousedown', ev => {
    const h = ev.target?.closest?.('#rh1, #rh2');
    if (!h) return;
    const p = panels();
    if (!p.left || !p.mid || !p.right) return;
    drag = { h, x: ev.clientX,
      lw: p.left.offsetWidth, mw: p.mid.offsetWidth, rw: p.right.offsetWidth };
    h.classList.add('drag');
    document.body.style.cursor = 'col-resize';
    ev.preventDefault();
  });

  document.addEventListener('mousemove', ev => {
    if (!drag) return;
    const p = panels();
    const dx = ev.clientX - drag.x;
    if (drag.h.id === 'rh1') {
      // Drag right → left wider; the middle pane absorbs the delta so the
      // total width stays constant.
      const nw = Math.max(180, Math.min(drag.lw + drag.mw - 180, drag.lw + dx));
      p.left.style.flex = `0 0 ${nw}px`;
      p.mid.style.flex = `0 0 ${drag.lw + drag.mw - nw}px`;
    } else {
      // rh2 sits at the right pane's LEFT edge: dragging right must SHRINK
      // the right pane (rw - dx). The middle pane absorbs the delta.
      const nw = Math.max(180, Math.min(drag.rw + drag.mw - 180, drag.rw - dx));
      p.right.style.flex = `0 0 ${nw}px`;
      p.mid.style.flex = `0 0 ${drag.rw + drag.mw - nw}px`;
    }
  });

  document.addEventListener('mouseup', () => {
    if (drag) {
      drag.h.classList.remove('drag');
      document.body.style.cursor = '';
      drag = null;
    }
  });

  // ── Chip-box vertical resize ───────────────────────────────────────
  // Drag handle under tall .fchips scroll boxes; sets an inline height
  // (survives until the section re-renders; the tall default returns).
  let vdrag = null;
  document.addEventListener('mousedown', ev => {
    const h = ev.target?.closest?.('.fchips-h');
    if (!h) return;
    const box = h.previousElementSibling;
    if (!box?.classList.contains('fchips')) return;
    vdrag = { box, h, y: ev.clientY, h0: box.offsetHeight };
    h.classList.add('drag');
    document.body.style.cursor = 'row-resize';
    ev.preventDefault();
  });
  document.addEventListener('mousemove', ev => {
    if (!vdrag) return;
    const max = Math.round(window.innerHeight * 0.6);
    vdrag.box.style.height =
      `${Math.max(48, Math.min(max, vdrag.h0 + ev.clientY - vdrag.y))}px`;
  });
  document.addEventListener('mouseup', () => {
    if (vdrag) {
      vdrag.h.classList.remove('drag');
      document.body.style.cursor = '';
      vdrag = null;
    }
  });
});
"""

# ═══════════════════════════════════════════════════════════════════════════
# App + State
# ═══════════════════════════════════════════════════════════════════════════

# Runs before first paint so the stored theme never flashes the wrong palette.
HEAD_JS = ("try{var ok=['dark','light','frost','midnight'];"
           "var t=localStorage.getItem('xv-theme');"
           "if(ok.indexOf(t)<0)t='frost';"
           "document.documentElement.setAttribute('data-theme',t);}catch(e){"
           "document.documentElement.setAttribute('data-theme','frost');}")

# htmx vendored (was fasthtml's htmxsrc → jsdelivr CDN): no runtime
# third-party script fetch; version pinned to 2.0.7 in static/htmx.min.js.
app = FastHTML(
    hdrs=(Script(HEAD_JS), Style(CSS), Script(src="/vendor/htmx.min.js"), Script(JS)),
    default_hdrs=False,
)
app.mount("/vendor", StaticFiles(directory=Path(__file__).resolve().parent / "static"))
rt = app.route

from urllib.parse import urlsplit  # noqa: E402
from starlette.datastructures import Headers, MutableHeaders  # noqa: E402
from starlette.responses import RedirectResponse, Response  # noqa: E402

# ── Local-tool hardening ──────────────────────────────────────────────────
# The app has no auth by design (personal tool on 127.0.0.1). These two
# middlewares close the realistic holes for that deployment: a random web
# page CSRF-ing the state-changing POSTs, and DNS rebinding turning a
# same-origin-looking attacker into a reader of the open spreadsheet.
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}

def _host_name(h):
    """Strip port from a Host header value; handles [::1]:8765."""
    if h.startswith("["):
        return h[1:h.index("]")] if "]" in h else h[1:]
    return h.rsplit(":", 1)[0] if ":" in h else h

def _host_ok(h):
    name = _host_name(h or "")
    # Loopback names always fine; test doubles like starlette's "testserver"
    # (dotless) fine; ONLY dotted external names (rebinding candidates) fail.
    return name in _LOOPBACK_HOSTS or "." not in name

class HostCsrfGuard:
    """Pure ASGI middleware (FastHTML exposes add_middleware, not the
    Starlette decorator). Rejects dotted external Host headers — the DNS
    rebinding candidate — and state-changing requests carrying a foreign
    Origin. Origin-less requests (curl, tests) pass: only browsers send
    Origin, and a browser WITH a foreign Origin is proof of cross-site."""

    def __init__(self, inner_app):
        self.inner = inner_app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.inner(scope, receive, send)
        headers = Headers(scope=scope)
        host = headers.get("host", "")
        if not _host_ok(host):
            return await Response("Forbidden", status_code=403)(scope, receive, send)
        if scope["method"] in ("POST", "PUT", "PATCH", "DELETE"):
            origin = headers.get("origin")
            if origin:
                netloc = urlsplit(origin).netloc
                if netloc and netloc != host:
                    return await Response("Forbidden", status_code=403)(scope, receive, send)
        return await self.inner(scope, receive, send)

_CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; "
        "connect-src 'self'; form-action 'self'; base-uri 'self'; "
        "object-src 'none'; frame-ancestors 'none'")

_SECURITY_HEADERS = {
    "Content-Security-Policy": _CSP,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "same-origin",
}

class SecurityHeaders:
    """Pure ASGI middleware adding security headers to every response."""

    def __init__(self, inner_app):
        self.inner = inner_app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.inner(scope, receive, send)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                h = MutableHeaders(raw=message["headers"])
                for k, v in _SECURITY_HEADERS.items():
                    h[k] = v
                message = {**message, "headers": h.raw}
            await send(message)

        return await self.inner(scope, receive, send_wrapper)

# Added first ⇒ innermost, so even 403s get security headers (headers wrap).
app.add_middleware(HostCsrfGuard)
app.add_middleware(SecurityHeaders)

S = dict(
    df=None, all_dfs={}, sheets=[], sheet="",
    filename="", cols=[], tc="", sc="",
    dc=[], fc=[], flt={}, ft={}, search="", sel=None, error=None,
    view_restored=False,
)

TH = 50  # unique values <= this → multi-select chips
MAX_ROWS = 500  # cap rows rendered to browser (DOM weight)
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
DC_DEFAULT = 10  # detail columns auto-selected on load; user can add more
# Shared by layout() and every #col-filters rebuild (OOB/swap), or the
# rebuilt pane loses its flex sizing.
FILTERS_STYLE = "overflow-y:auto;flex:1;padding-top:6px;"
FC_DEFAULT = 10  # filterable columns auto-selected on load; user picks via picker
# Per-file/sheet saved views (explicit Save, auto-restore on upload/sheet).
# Module constant so tests can redirect it. Structure:
#   { filename: { sheet: {tc,sc,dc,fc,flt,ft,search,saved_at} } }
# Filename is only ever a JSON dict key, never a filesystem path.
VIEWS_FILE = Path(__file__).resolve().parent / "saved_views.json"


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def load_views():
    try:
        with open(VIEWS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}

def save_views(views):  # atomic: tmp + rename
    tmp = VIEWS_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(views, f, ensure_ascii=False, indent=1)
    tmp.replace(VIEWS_FILE)

def saved_view_for(fn, sheet):
    return load_views().get(fn, {}).get(sheet)

def current_view():
    return {"tc": S["tc"], "sc": S["sc"], "dc": list(S["dc"]), "fc": list(S["fc"]),
            "flt": {c: sorted(v) for c, v in S["flt"].items()},
            "ft": dict(S["ft"]), "search": S["search"],
            "saved_at": time.strftime("%Y-%m-%d %H:%M")}

def apply_view(view):
    """Restore a saved view into S, validated against the sheet's real
    columns: stale column names are dropped, bad tc/sc fall back."""
    cols = S["cols"]
    S["tc"] = view.get("tc") if view.get("tc") in cols else (cols[0] if cols else "")
    sc = view.get("sc", "")
    S["sc"] = sc if (not sc or sc in cols) else ""
    # "in view" distinguishes an intentionally emptied dc/fc from no key.
    S["dc"] = [c for c in view.get("dc", cols) if c in cols] if "dc" in view else cols[:DC_DEFAULT]
    S["fc"] = [c for c in view.get("fc", cols) if c in cols] if "fc" in view else cols[:FC_DEFAULT]
    S["flt"] = {c: set(map(str, vals)) for c, vals in (view.get("flt") or {}).items() if c in S["fc"]}
    S["ft"] = {c: str(t) for c, t in (view.get("ft") or {}).items() if c in S["fc"] and t}
    S["search"] = str(view.get("search") or "")
    S["sel"] = None

_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

def export_cols():
    """Column order for export: title, sub, then detail columns (deduped)."""
    out = []
    for c in (S["tc"], S["sc"], *S["dc"]):
        if c in S["cols"] and c not in out:
            out.append(c)
    return out or S["cols"]

def export_filename(fmt):
    stem = Path(S["filename"]).stem
    base = f"{stem}_{S['sheet']}" if S["sheet"] else stem
    base = re.sub(r"[^\w. -]+", "_", base).strip() or "export"
    return f"{base}.{fmt}"

def export_response(fmt):
    """Current view (filtered rows, view columns) as a downloadable CSV/XLSX."""
    f = filt()[export_cols()]
    if fmt == "csv":
        # utf-8-sig BOM so Excel opens UTF-8 CSVs directly.
        body, media = f.to_csv(index=False).encode("utf-8-sig"), "text/csv"
    else:
        buf = BytesIO()
        f.to_excel(buf, index=False, engine="openpyxl")
        body, media = buf.getvalue(), _XLSX_MIME
    cd = f"attachment; filename*=UTF-8''{quote(export_filename(fmt))}"
    return Response(body, media_type=media, headers={"Content-Disposition": cd})

def sv(v):
    return "" if pd.isna(v) else str(v)

def form_cols(form, key):
    """Checkbox values for column pickers, matched back to S["cols"].
    Browsers normalize LF to CRLF when submitting control values, so real
    multi-line column names ("Legacy\\nSCF #") must be normalized back."""
    out = []
    for v in form.getlist(key):
        v = str(v).replace("\r\n", "\n")
        if v in S["cols"] and v not in out:
            out.append(v)
    return out

def normalize_df(df):
    """Give every loaded sheet a stable, unique row id for the session."""
    return df.reset_index(drop=True)

def sync_selection(frame):
    if S["sel"] is not None and S["sel"] not in frame.index:
        S["sel"] = None

def filt():
    if S["df"] is None:
        return pd.DataFrame()
    r = S["df"]
    mask = pd.Series(True, index=r.index)
    q = S["search"].strip().lower()
    if q:
        search_mask = pd.Series(False, index=r.index)
        for c in r.columns:
            search_mask |= r[c].astype(str).str.lower().str.contains(q, na=False, regex=False)
        mask &= search_mask
    for col, vals in S["flt"].items():
        if col in r.columns and vals:
            mask &= r[col].astype(str).isin(vals)
    for col, txt in S["ft"].items():
        if col in r.columns and txt:
            mask &= r[col].astype(str).str.lower().str.contains(txt.lower(), na=False, regex=False)
    return r.loc[mask]


# ═══════════════════════════════════════════════════════════════════════════
# Components
# ═══════════════════════════════════════════════════════════════════════════

def sect(lbl, *ch):
    return Div(Label(lbl, cls="slbl"), *ch, cls="sect")

def upload():
    loaded = S["filename"] != ""
    error = S.get("error", "")
    if error:
        buttons = [Button("Upload Another", hx_post="/close", hx_target="#app", hx_swap="outerHTML",
                          cls="btn bxs bp mt6")]
        if S["df"] is not None:
            # A good file is still loaded — let the user dismiss the error
            # without wiping it.
            buttons.insert(0, Button("Keep Current File", hx_post="/clear-error", hx_target="#app",
                                     hx_swap="outerHTML", cls="btn bxs mt6"))
        return sect("File", Div(
            Span("⚠️", cls="dz-i"), P(error, cls="dz-f", style="color:var(--danger);"),
            Div(*buttons, style="display:flex;gap:4px;justify-content:center;"),
            style="border:1px solid var(--border);border-radius:var(--r);padding:14px;text-align:center;background:var(--dz-bg);",
        ))
    if loaded:
        return sect("File", Div(
            Span("📂", cls="dz-i"), P(S["filename"], cls="dz-f"),
            Form(
                Input(type="file", name="file", accept=".xlsx,.xls,.csv", id="fi", hidden=True),
                Div(
                    Button("Change", type="button", data_open_file="true", cls="btn bxs"),
                    Button("Close", hx_post="/close", hx_target="#app", hx_swap="outerHTML", cls="btn bxs bc"),
                    style="display:flex;gap:4px;margin-top:8px;",
                ),
                hx_post="/upload", hx_target="#app", hx_swap="outerHTML", hx_include="#fi",
                hx_encoding="multipart/form-data", id="upload-form",
            ),
            style="border:1px solid var(--border);border-radius:var(--r);padding:14px;text-align:center;background:var(--dz-bg);",
        ))
    return sect("File",
        Div(Span("📂", cls="dz-i"), P("Drop an Excel or CSV file or click", cls="dz-t"),
            cls="dz", id="dropzone"),
        Form(
            Input(type="file", name="file", accept=".xlsx,.xls,.csv", id="fi", hidden=True),
            Button("Upload", type="submit", cls="btn bp wf mt6"),
            hx_post="/upload", hx_target="#app", hx_swap="outerHTML", hx_include="#fi",
            hx_encoding="multipart/form-data", id="upload-form",
        ),
    )

def sheets():
    if not S["sheets"]: return Div()
    return sect("Sheet", Div(
        *(Button(n, cls=f"stab{' on' if n==S['sheet'] else ''}",
                 hx_post="/sheet", hx_target="#app", hx_swap="outerHTML",
                 name="s", value=n) for n in S["sheets"]),
        cls="stabs"
    ))

def title_pick():
    if not S["cols"]: return Div()
    return sect("Title Column",
        Select(*(Option(c, value=c, selected=(c==S["tc"])) for c in S["cols"]),
               name="tc", hx_post="/cfg", hx_target="#main-wrap", hx_swap="outerHTML", hx_trigger="change"))

def sub_pick():
    if not S["cols"]: return Div()
    return sect("Subtitle Column",
        Select(Option("\u2014 none \u2014", value=""),
               *(Option(c, value=c, selected=(c==S["sc"])) for c in S["cols"]),
               name="sc", hx_post="/cfg", hx_target="#main-wrap", hx_swap="outerHTML", hx_trigger="change"))

def search_box():
    if S["df"] is None:
        return Div()
    return Form(
        sect("Search", Input(type="search", name="search",
            placeholder="Search all columns\u2026", value=S["search"],
            hx_post="/apply", hx_target="#main-wrap", hx_swap="outerHTML",
            hx_trigger="input changed delay:200ms")),
        id="filter-form", hx_post="/apply", hx_target="#main-wrap", hx_swap="outerHTML",
    )

def detail_pick():
    if not S["cols"]: return Div()
    dc = S.get("dc", [])
    chips = [Label(Input(type="checkbox", name="dc", value=c, checked=(c in dc)),
                         c, cls=f"chip{' on' if c in dc else ''}") for c in S["cols"]]
    tall = len(S["cols"]) > 12
    return Div(sect("Detail Columns",
        Form(
            Div(
                Button("All", cls="btn bxs", data_sel="", type="button"),
                Button("Clear", cls="btn bxs", data_clear="", type="button"),
                style="display:flex;gap:3px;margin-bottom:4px;",
            ),
            Div(*chips, cls=f"fchips{' tall' if tall else ''}"),
            *( [Div(cls="fchips-h")] if tall else [] ),
            Input(type="hidden", name="dc_present", value="1"),
            Button("Apply", cls="btn bxs bp wf mt4"),
            hx_post="/cfg/detail-cols", hx_target="#detail",
        ),
    ), id="detail-pick")

def filter_pick():
    """Which columns get a filter group below — same chip/Apply pattern as
    detail_pick. Lists ALL columns (explicit selection beats the old
    tc/sc skip). #fc-search narrows the chips client-side."""
    if S["df"] is None or not S["cols"]: return Div()
    fc = S.get("fc", [])
    chips = [Label(Input(type="checkbox", name="fc", value=c, checked=(c in fc)),
                         c, cls=f"chip{' on' if c in fc else ''}") for c in S["cols"]]
    tall = len(S["cols"]) > 12
    return Div(sect("Filter Columns",
        Input(type="search", id="fc-search", placeholder="Search columns…",
              autocomplete="off", aria_label="Filter column picker",
              style="margin-bottom:6px;"),
        Form(
            Div(
                Button("All", cls="btn bxs", data_sel="", type="button"),
                Button("Clear", cls="btn bxs", data_clear="", type="button"),
                style="display:flex;gap:3px;margin-bottom:4px;",
            ),
            Div(*chips, cls=f"fchips{' tall' if tall else ''}", id="fc-chips"),
            *( [Div(cls="fchips-h")] if tall else [] ),
            Input(type="hidden", name="fc_present", value="1"),
            Button("Apply", cls="btn bxs bp wf mt4"),
            hx_post="/cfg/filter-cols", hx_target="#col-filters", hx_swap="outerHTML",
        ),
    ), id="filter-pick")

def saved_view_section():
    """Save/Update/Forget the view for the CURRENT file+sheet; the endpoints
    re-render this section in place (outerHTML swap on #saved-view)."""
    if S["df"] is None: return Div(id="saved-view")
    saved = (load_views().get(S["filename"]) or {}).get(S["sheet"])
    if saved:
        content = [
            Span(f"✓ saved {saved.get('saved_at', '')}", cls="dim",
                 style="font-size:11px;color:var(--dim);"),
            Button("Update view", hx_post="/view/save", hx_target="#saved-view",
                   hx_swap="outerHTML", cls="btn bxs bp"),
            Button("Forget", hx_post="/view/forget", hx_target="#saved-view",
                   hx_swap="outerHTML", cls="btn bxs bc"),
        ]
    else:
        content = [Button("Save view", hx_post="/view/save", hx_target="#saved-view",
                          hx_swap="outerHTML", cls="btn bxs bp")]
    if S.get("view_restored"):
        content.insert(0, Div("Saved view restored",
                              style="font-size:11px;color:var(--accent);margin-bottom:3px;"))
    return Div(sect("Saved View",
        Div(*content, style="display:flex;gap:5px;align-items:center;flex-wrap:wrap;"),
        P(S["filename"], style="font-size:10px;color:var(--muted);margin-top:3px;"
          f"{' ; sheet: ' + S['sheet'] if S['sheet'] else ''}"),
    ), id="saved-view")

def export_section():
    """Download the current view (filtered rows, view columns) as CSV/Excel."""
    if S["df"] is None: return Div(id="export-sec")
    n = len(filt())
    return Div(sect("Export",
        Div(A("CSV", href="/export/csv", cls="btn bxs bp"),
            A("Excel", href="/export/xlsx", cls="btn bxs bp"),
            style="display:flex;gap:5px;"),
        P(f"{n} filtered row{'s' if n != 1 else ''}", id="export-count",
          style="font-size:10px;color:var(--muted);margin-top:3px;"),
    ), id="export-sec")

# ═══════════════════════════════════════════════════════════════════════════
# Filter groups (sidebar)
# Wide sheets made the sidebar non-responsive: eagerly rendering a group per
# column meant 400+ groups and thousands of checkboxes shipped in every #app
# swap. Sidebar now renders cheap collapsed stubs (no pandas access at all);
# the real chip/text controls are fetched by GET /filter/{idx} on first
# expand. Column identity travels as an index into S["cols"], never a raw
# name in the URL.
# ═══════════════════════════════════════════════════════════════════════════

def col_filters():
    if S["df"] is None or not S["cols"]: return Div()
    gs = []
    for i, col in enumerate(S["cols"]):
        # Only columns explicitly picked in the Filter Columns picker get a
        # group; explicit selection overrides the old tc/sc skip.
        if col not in S.get("fc", []): continue
        nsel = len(S["flt"].get(col) or ())
        badge = Span(f"{nsel} selected", cls="fgrp-on") if nsel else (
            Span("text filter", cls="fgrp-on") if S["ft"].get(col) else None)
        summary = Summary(Span(f"Filter: {col}", cls="fgrp-t"),
                          *( [badge] if badge else [] ))
        # <summary> stays outside the swap target: swapping the <details>'s
        # own innerHTML would destroy the disclosure element.
        gs.append(Details(
            summary,
            Div(id=f"fgb-{i}", cls="fgrp-body"),
            cls="fgrp", hx_get=f"/filter/{i}", hx_trigger="toggle once",
            hx_target=f"#fgb-{i}", hx_swap="innerHTML",
        ))
    if not gs:
        gs.append(Div("No filter columns selected.", cls="empty"))
    # Caption content ("Showing X of Y" + show-more button) is managed by the
    # sidebar cap JS; the server only ships the placeholder.
    gs.append(Div(id="colf-more", cls="colf-more"))
    return Div(*gs)

def filter_group_body(col):
    """The expandable body of one filter group: chip form (low cardinality)
    or text input (high cardinality). Loaded lazily into #fgb-{idx}."""
    n = int(S["df"][col].dropna().nunique())
    cv = S["flt"].get(col, set())
    ct = S["ft"].get(col, "")
    if n <= TH:
        vals = sorted(S["df"][col].dropna().unique()[:100], key=lambda x: str(x))
        chips = [Label(
            Input(type="checkbox", name=f"f_{col}", value=str(v), checked=(str(v) in cv)),
            str(v), cls=f"chip{' on' if str(v) in cv else ''}"
        ) for v in vals]
        return Form(
            Div(Button("All", cls="btn bxs", data_sel="", type="button"),
                Button("Clear", cls="btn bxs", data_clear="", type="button"),
                style="display:flex;gap:3px;margin-bottom:3px;"),
            Div(*chips, cls=f"fchips{' tall' if len(vals) > 12 else ''}"),
            *( [Div(cls="fchips-h")] if len(vals) > 12 else [] ),
            Input(type="hidden", name=f"f_{col}_present", value="1"),
            Button("Apply", cls="btn bxs bp wf mt4"),
            hx_post="/apply", hx_target="#main-wrap", hx_swap="outerHTML",
            hx_include="#filter-form", data_autosubmit="true",
        )
    return Input(type="text", name=f"ft_{col}", placeholder=f"Filter {col}\u2026",
                 value=ct, hx_post="/apply", hx_target="#main-wrap",
                 hx_swap="outerHTML", hx_trigger="input changed delay:250ms",
                 hx_include="#filter-form", style="margin-top:3px;")

def row_cards(df):
    if S["df"] is None:
        return [Div("Upload a file to start browsing rows.", cls="empty")]
    if df.empty: return [Div("No matching rows.", cls="empty")]
    cap = min(len(df), MAX_ROWS)
    cards = []
    for row_id, row in df.head(cap).iterrows():
        t = sv(row.get(S["tc"], "")) or f"Row {row_id + 1}"
        sub = sv(row.get(S["sc"], "")) if S["sc"] else ""
        sub_el = Div(sub, cls="rsub") if sub else Div()
        sel = " sel" if S["sel"] == row_id else ""
        cards.append(Div(
            Div(t, cls="rtitle"), sub_el, Div(f"Row {row_id + 1}", cls="ridx"),
            cls=f"rcard{sel}", tabindex="0", role="button",
            hx_get=f"/row/{row_id}", hx_target="#detail", hx_trigger="click",
        ))
    if len(df) > MAX_ROWS:
        cards.append(Div(f"Showing first {MAX_ROWS} of {len(df)} rows. Narrow your search.",
                         cls="empty", style="margin-top:12px;color:var(--accent);"))
    return cards

def row_list(df):
    return Div(*row_cards(df), cls="pnb", id="main-wrap")

def row_refresh(frame=None):
    if frame is None:
        frame = filt()
    sync_selection(frame)
    total = len(S["df"]) if S["df"] is not None else 0
    return (
        row_list(frame),
        Span(f"{len(frame)} of {total} rows", id="row-count", hx_swap_oob="true"),
        # Keep the sidebar Export section's count in step with the swap.
        P(f"{len(frame)} filtered row{'s' if len(frame) != 1 else ''}",
          id="export-count", hx_swap_oob="true",
          style="font-size:10px;color:var(--muted);margin-top:3px;"),
        # The selected row may have been filtered out (sync_selection cleared
        # it) — reset the detail pane in lockstep so it never shows a row
        # that is no longer in the list.
        Div(detail_view(S["sel"]), cls="pnb", id="detail", hx_swap_oob="true"),
    )

def detail_view(row_i):
    if row_i is None or S["df"] is None:
        return Div(Div(Span("\U0001f4cb", cls="ic"), H2("Select a Row"),
                       P("Click any row to inspect details."), cls="welcome"))
    if row_i not in S["df"].index:
        return Div(Div(Span("\U0001f4cb", cls="ic"), H2("Select a Row"),
                       P("This row is no longer available."), cls="welcome"))
    row = S["df"].loc[row_i]
    cells = []
    for c in S["dc"]:
        value = sv(row.get(c, ""))
        cells.append(Div(
            Div(Div(c, cls="lbl"), Button("Copy", type="button", cls="copy-btn",
                                           data_copy_value=value, title=f"Copy {c}"), cls="dhead"),
            Div(value, cls="val"), cls="dcell"))
    if not cells:
        cells = [P("No detail columns selected.", cls="empty")]
    return Div(
        H4(f"Row {row_i + 1}", style="font-family:var(--font-serif);font-size:14px;font-weight:600;margin-bottom:10px;color:var(--txt2)"),
        Div(*cells, cls="dgrid"),
    )

# ═══════════════════════════════════════════════════════════════════════════
# Layout
# ═══════════════════════════════════════════════════════════════════════════

THEMES = {  # data-theme key: (display name, popover swatch panel bg, swatch accent)
    "dark":     ("Ink",       "#1b1e24", "#c9a45c"),
    "light":    ("Paper",     "#fbfaf6", "#8a6a1f"),
    "frost":    ("Frost",     "#ffffff", "#0071e3"),
    "midnight": ("Midnight",  "#1c1c1e", "#0a84ff"),
}

def settings_pop():
    # Feather "settings" icon (MIT), stroke-based so it picks up --dim.
    gear = Svg(
        Circle(cx="12", cy="12", r="3"),
        SvgPath(d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0"
             " 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21"
             "a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0"
             " 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65"
             " 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0"
             " 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2"
             " 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1"
             ".65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0"
             " 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0"
             " 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51"
             " 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"),
        viewBox="0 0 24 24", width="14", height="14", fill="none",
        stroke="currentColor", stroke_width="2", stroke_linecap="round",
        stroke_linejoin="round", aria_hidden="true")
    rows = [Div(Span(cls="tsw", style=f"background:{bg};box-shadow:inset 0 0 0 2px {ac}"),
                name, Span("✓", cls="tck"), data_theme_opt=key, cls="topt")
            for key, (name, bg, ac) in THEMES.items()]
    return Button(gear, id="settings-btn", type="button", cls="theme-btn",
                  aria_label="Settings", title="Theme"), \
           Div(Div("Theme", cls="tpop-h"), *rows, cls="tpop", id="theme-pop")

def layout(f=None):
    if f is None: f = filt()
    sync_selection(f)
    total = len(S["df"]) if S["df"] is not None else 0
    cnt = len(f)
    return Div(
        # ── Left: Sidebar ─────────────────────────────────────────────
        Div(
            Div(Span("Sieve", cls="stitle"),
                P(S["sheet"], cls="ssub") if S["sheet"] else Div(),
                *settings_pop(),
                cls="pnh"),
            Div(
                upload(), sheets(), title_pick(), sub_pick(), search_box(),
                detail_pick(), filter_pick(), saved_view_section(), export_section(),
                Div(
                    Label("Filters", cls="slbl"),
                    Div(col_filters(), id="col-filters", style=FILTERS_STYLE),
                    style="flex:1;display:flex;flex-direction:column;min-height:0;",
                ),
                cls="pnb", id="sidebar"),
            cls="pnl", style="flex:0 0 220px;", id="pnl-left"),
        # ── Resize handle ──────────────────────────────────────────────
        Div(cls="rh", id="rh1"),
        # ── Middle: Row list ──────────────────────────────────────────
        Div(
            Div(
                Span(f"{cnt} of {total} rows", cls="count", id="row-count"),
                Span(f"Sheet: {S['sheet']}") if S["sheet"] else Span(""),
                cls="rbar"),
            row_list(f),
            cls="pnl", style="flex:0 0 360px;", id="pnl-mid"),
        # ── Resize handle ──────────────────────────────────────────────
        Div(cls="rh", id="rh2"),
        # ── Right: Detail ─────────────────────────────────────────────
        Div(
            Div(Span("Details", cls="stitle"), cls="pnh"),
            Div(detail_view(S["sel"]), cls="pnb", id="detail"),
            cls="pnl", style="flex:1;", id="pnl-right"),
        cls="app", id="app")


# ═══════════════════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════════════════

@rt("/")
def get():
    return layout()

_MULTIPART_SLACK = 64 * 1024  # framing overhead around the file part

@rt("/upload", methods=["POST"])
def post(req: Request, file: File):
    # Reject on declared size BEFORE buffering, then cap the read itself —
    # an oversized body must never land fully in memory.
    cl = req.headers.get("content-length", "")
    if cl.isdigit() and int(cl) > MAX_FILE_SIZE + _MULTIPART_SLACK:
        S["error"] = f"File too large. Max {MAX_FILE_SIZE//(1024*1024)}MB."
        return layout()
    data = file.file.read(MAX_FILE_SIZE + 1)
    file.file.close()  # release the spooled temp file promptly
    if len(data) > MAX_FILE_SIZE:
        S["error"] = f"File too large. Max {MAX_FILE_SIZE//(1024*1024)}MB."
        return layout()
    ext = Path(file.filename).suffix.lower()
    if ext not in (".csv", ".xls", ".xlsx"):
        S["error"] = "Unsupported file type. Upload .xlsx, .xls, or .csv."
        return layout()
    try:
        if ext == ".csv":
            df = pd.read_csv(BytesIO(data))
            S["all_dfs"] = {"Sheet1": normalize_df(df)}
        else:
            # sheet_name=None parses the workbook ONCE and returns every
            # sheet — twice as fast as ExcelFile + per-sheet read_excel.
            S["all_dfs"] = {s: normalize_df(d) for s, d in pd.read_excel(BytesIO(data), sheet_name=None).items()}
        S["sheets"] = list(S["all_dfs"].keys())
    except Exception as e:
        S["error"] = f"Error reading file: {e}"
        return layout()

    S["error"] = None

    S["sheet"] = S["sheets"][0]
    S["df"] = S["all_dfs"][S["sheet"]]
    S["filename"] = file.filename
    S["cols"] = list(S["df"].columns)
    S["tc"] = S["cols"][0] if S["cols"] else ""
    S["sc"] = S["cols"][1] if len(S["cols"]) > 1 else ""
    S["dc"] = S["cols"][:DC_DEFAULT]
    S["fc"] = S["cols"][:FC_DEFAULT]
    S["flt"] = {}; S["ft"] = {}; S["search"] = ""; S["sel"] = None
    S["view_restored"] = False
    v = saved_view_for(S["filename"], S["sheet"])
    if v:
        apply_view(v)
        S["view_restored"] = True
    return layout()

@rt("/close", methods=["POST"])
def post():
    for k in ("df","all_dfs","sheets","sheet","filename","cols","tc","sc","dc","fc","flt","ft","search","sel","error","view_restored"):
        S[k] = {} if k in ("all_dfs","flt","ft") else [] if k in ("sheets","cols","dc","fc") \
              else "" if k in ("sheet","filename","tc","sc","search","error") else None
    return layout()

@rt("/clear-error", methods=["POST"])
def post():
    """Dismiss an upload error while keeping the currently loaded file."""
    S["error"] = None
    return layout()

@rt("/view/save", methods=["POST"])
def post():
    """Persist the current view state for this file+sheet as JSON."""
    if S["df"] is None:
        return saved_view_section()
    views = load_views()
    views.setdefault(S["filename"], {})[S["sheet"]] = current_view()
    save_views(views)
    return saved_view_section()

@rt("/view/forget", methods=["POST"])
def post():
    """Delete the saved view for this file+sheet."""
    views = load_views()
    if S["sheet"] in views.get(S["filename"], {}):
        del views[S["filename"]][S["sheet"]]
        if not views[S["filename"]]:
            del views[S["filename"]]
        save_views(views)
    return saved_view_section()

@rt("/export/{fmt}")
def get(fmt: str):
    """Download the current view (filtered rows, view columns) as CSV/Excel."""
    if S["df"] is None:
        return RedirectResponse("/", status_code=303)
    if fmt not in ("csv", "xlsx"):
        return Response("Not found", status_code=404)
    return export_response(fmt)

@rt("/sheet", methods=["POST"])
def post(s: str):
    if s not in S["all_dfs"]: return Div("Invalid.", cls="empty", id="main-wrap")
    S["sheet"] = s
    S["df"] = S["all_dfs"][s]
    S["cols"] = list(S["df"].columns)
    S["tc"] = S["cols"][0] if S["cols"] else ""
    S["sc"] = S["cols"][1] if len(S["cols"]) > 1 else ""
    S["dc"] = S["cols"][:DC_DEFAULT]
    S["fc"] = S["cols"][:FC_DEFAULT]
    S["flt"] = {}; S["ft"] = {}; S["search"] = ""; S["sel"] = None
    S["view_restored"] = False
    v = saved_view_for(S["filename"], s)
    if v:
        apply_view(v)
        S["view_restored"] = True
    return layout()

@rt("/cfg", methods=["POST"])
async def post(req: Request):
    form = await req.form()
    if "tc" in form and form.get("tc") in S["cols"]:
        S["tc"] = form.get("tc")
    if "sc" in form:
        S["sc"] = form.get("sc") if form.get("sc") in S["cols"] else ""
    # col_filters() skips the title/subtitle columns at render time, so a
    # tc/sc change must rebuild the sidebar filter groups out-of-band —
    # otherwise the new title keeps a redundant filter and the demoted
    # column never gets one.
    return (*row_refresh(),
            Div(col_filters(), id="col-filters", style=FILTERS_STYLE,
                hx_swap_oob="true"))

@rt("/cfg/detail-cols", methods=["POST"])
async def post(req: Request):
    """Update detail columns without replacing entire app."""
    form = await req.form()
    dc_present = form.get("dc_present")
    if dc_present is not None:
        S["dc"] = form_cols(form, "dc")  # ALL checked, matched back to S["cols"]
    return detail_view(S["sel"])

@rt("/cfg/filter-cols", methods=["POST"])
async def post(req: Request):
    """Update filterable columns; rebuild the filter group list in place."""
    form = await req.form()
    if form.get("fc_present") is not None:
        chosen = set(form_cols(form, "fc"))
        # Deselecting a column also drops its active filter values, so a
        # hidden column never silently keeps filtering rows.
        for c in set(S["fc"]) - chosen:
            S["flt"].pop(c, None); S["ft"].pop(c, None)
        S["fc"] = [c for c in S["cols"] if c in chosen]  # stable column order
    return Div(col_filters(), id="col-filters", style=FILTERS_STYLE)

@rt("/apply", methods=["POST"])
async def post(req: Request):
    form = await req.form()
    if "search" in form:
        S["search"] = str(form.get("search") or "")
    for col in S["cols"]:
        filter_key = f"f_{col}"
        if f"{filter_key}_present" in form:
            vals = form.getlist(filter_key)
            if vals:
                S["flt"][col] = set(vals)
            else:
                S["flt"].pop(col, None)
        text_key = f"ft_{col}"
        if text_key in form:
            value = str(form.get(text_key) or "")
            if value:
                S["ft"][col] = value
            else:
                S["ft"].pop(col, None)
    return row_refresh()


@rt("/row/{idx}")
def get(idx: int):
    if S["df"] is None or idx < 0 or idx not in S["df"].index:
        return detail_view(None)
    S["sel"] = idx
    return detail_view(idx)

@rt("/filter/{idx}")
def get(idx: int):
    """Lazy body of one sidebar filter group (idx into S["cols"])."""
    if S["df"] is None or idx < 0 or idx >= len(S["cols"]):
        return Div()
    return filter_group_body(S["cols"][idx])


# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)