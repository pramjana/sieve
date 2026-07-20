"""
Excel Viewer — dark glass-morphism UI, FastHTML + HTMX, pandas.
Upload → filter → browse → inspect rows.
"""

from pathlib import Path
from io import BytesIO

import pandas as pd
from fasthtml.common import (
    FastHTML, Style, Script, File, htmxsrc, Request,
    Button, Div, Form, H2, H4, Input,
    Label, Option, P, Select, Span,
)

# ═══════════════════════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════════════════════

CSS = r"""
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0b0818;--bg2:#1e1540;--accent:#a855f7;--accent2:#7c3aed;
  --glow:rgba(168,85,247,.2);--glow2:rgba(168,85,247,.45);
  --glass:rgba(255,255,255,.04);--glass2:rgba(255,255,255,.07);
  --border:rgba(255,255,255,.08);--border2:rgba(255,255,255,.16);
  --txt:#e4daf0;--txt2:#f0e8fa;--dim:#7b6f96;--muted:#5a4f72;
  --danger:#f43f5e;--success:#34d399;--r:10px;--rs:6px;
}
html,body{height:100%;width:100%;font-family:'Inter','Segoe UI',system-ui,sans-serif;
  background:linear-gradient(160deg,var(--bg),var(--bg2) 40%,#0f0a24);color:var(--txt);font-size:14px}

/* Layout */
.app{display:flex;height:100vh;padding:0 10px}
.pnl{display:flex;flex-direction:column;overflow:hidden;background:var(--glass);
  backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);
  border:1px solid var(--border);border-radius:var(--r);box-shadow:0 4px 24px rgba(0,0,0,.25);
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
.pnh{padding:14px 16px;border-bottom:1px solid var(--border);flex-shrink:0}
.pnb{flex:1;overflow-y:auto;padding:12px}
.pnb::-webkit-scrollbar{width:5px}
.pnb::-webkit-scrollbar-track{background:0 0}
.pnb::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
.pnb::-webkit-scrollbar-thumb:hover{background:var(--border2)}

/* Sidebar */
.stitle{font-size:15px;font-weight:700;color:var(--accent);letter-spacing:-.3px}
.ssub{font-size:10px;color:var(--muted);margin-top:2px}
.sect{margin-bottom:14px}
.slbl{display:block;font-size:10px;font-weight:600;text-transform:uppercase;
  letter-spacing:1px;color:var(--muted);margin-bottom:5px}

/* Upload */
.dz{border:2px dashed var(--border);border-radius:var(--r);padding:20px 12px;
  text-align:center;cursor:pointer;transition:all .2s;background:rgba(0,0,0,.15)}
.dz:hover,.dz.on{border-color:var(--accent);background:var(--glow)}
.dz-i{font-size:32px;display:block;margin-bottom:4px}
.dz-t{font-size:12px;color:var(--dim)}
.dz-f{font-size:11px;color:var(--accent);margin-top:6px;word-break:break-all}

/* Buttons */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:5px;
  padding:7px 12px;border:1px solid var(--border);border-radius:var(--rs);
  background:var(--glass2);color:var(--txt);font-size:12px;font-weight:500;
  cursor:pointer;transition:all .15s;text-decoration:none;font-family:inherit}
.btn:hover{background:rgba(255,255,255,.1);border-color:var(--border2)}
.bp{background:var(--accent);border-color:var(--accent);color:#fff}
.bp:hover{background:var(--accent2)}
.bxs{padding:2px 8px;font-size:10px}
.bc{border-color:rgba(244,63,94,.3);color:var(--danger)}
.bc:hover{background:rgba(244,63,94,.12)}

/* Inputs */
input[type="text"],input[type="search"],select{width:100%;padding:7px 10px;
  border:1px solid var(--border);border-radius:var(--rs);
  background:rgba(0,0,0,.3);color:var(--txt);font-size:12px;
  font-family:inherit;outline:none;transition:border-color .15s,box-shadow .15s}
input:focus,select:focus{border-color:var(--accent);box-shadow:0 0 0 2px var(--glow)}
select{cursor:pointer}
select option{background:var(--bg2);color:var(--txt)}

/* Sheet tabs */
.stabs{display:flex;flex-wrap:wrap;gap:3px}
.stab{padding:5px 10px;border-radius:var(--rs);border:1px solid var(--border);
  background:0 0;color:var(--dim);font-size:11px;font-family:inherit;cursor:pointer;transition:all .15s}
.stab:hover{border-color:var(--accent);color:var(--txt)}
.stab.on{background:var(--accent);border-color:var(--accent);color:#fff}

/* Row cards */
.rcard{padding:10px 12px;border-radius:var(--rs);border:1px solid transparent;
  cursor:pointer;transition:all .12s;margin-bottom:3px}
.rcard:hover{background:rgba(255,255,255,.06);border-color:var(--border)}
.rcard.sel{background:var(--glow);border-color:var(--accent)}
.rcard:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
.rtitle{font-size:13px;font-weight:600;color:var(--txt2);white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis}
.rsub{font-size:11px;color:var(--dim);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ridx{font-size:9px;color:var(--muted);margin-top:1px}

/* Detail grid */
.dgrid{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.dcell{padding:8px 10px;border-radius:var(--rs);background:rgba(0,0,0,.18);
  border:1px solid var(--border)}
.dcell .lbl{font-size:9px;font-weight:600;text-transform:uppercase;
  letter-spacing:.7px;color:var(--muted);margin-bottom:3px}
.dcell .val{font-size:12px;word-break:break-word;color:var(--txt2);line-height:1.4}
.dcell .val:empty::before{content:"\2014";color:var(--muted)}
.dhead{display:flex;align-items:center;justify-content:space-between;gap:6px}
.copy-btn{padding:1px 5px;border:1px solid var(--border);border-radius:3px;
  background:transparent;color:var(--dim);font:inherit;font-size:9px;cursor:pointer}
.copy-btn:hover,.copy-btn:focus-visible{border-color:var(--accent);color:var(--txt)}

/* Chips */
.fgrp{margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid rgba(255,255,255,.03)}
.fgrp-t{font-size:11px;font-weight:600;color:var(--dim);margin-bottom:4px}
.fchips{display:flex;flex-wrap:wrap;gap:3px;max-height:80px;overflow-y:auto}
.chip{display:inline-flex;align-items:center;gap:2px;padding:2px 7px;
  border-radius:3px;border:1px solid var(--border);font-size:10px;
  cursor:pointer;transition:all .12s;background:0 0;color:var(--dim);user-select:none}
.chip:hover{border-color:var(--accent);color:var(--txt)}
.chip.on{background:var(--accent);border-color:var(--accent);color:#fff}
.chip input{display:none}

/* Result bar */
.rbar{display:flex;align-items:center;justify-content:space-between;
  font-size:10px;color:var(--muted);padding:6px 14px;
  border-bottom:1px solid var(--border);flex-shrink:0}
.rbar span{display:flex;align-items:center;gap:4px}

/* Welcome/empty */
.welcome{display:flex;flex-direction:column;align-items:center;justify-content:center;
  height:100%;text-align:center;color:var(--dim)}
.welcome .ic{font-size:48px;margin-bottom:12px}
.welcome h2{font-size:17px;color:var(--txt);margin-bottom:6px}
.welcome p{font-size:12px;max-width:260px;line-height:1.6}
.empty{text-align:center;padding:24px;color:var(--muted);font-size:12px}

/* Animations */
@keyframes fadeIn{from{opacity:0;transform:translateY(-2px)}to{opacity:1;transform:none}}
@keyframes spin{to{transform:rotate(360deg)}}
.htmx-added{animation:fadeIn .15s ease}

/* Loading indicator */
.loading-overlay{
  position:fixed;top:0;left:0;right:0;bottom:0;
  background:rgba(11,8,24,0.7);backdrop-filter:blur(4px);
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
    if (form && !form.closest('#detail-pick')) form.requestSubmit();
  });

  // The loaded-state Change control opens the existing hidden file input.
  document.addEventListener('click', ev => {
    const opener = ev.target.closest('[data-open-file]');
    if (!opener) return;
    opener.closest('form')?.querySelector('input[type="file"]')?.click();
  });
  document.addEventListener('change', ev => {
    if (ev.target.matches('#fi') && ev.target.files.length) ev.target.form?.requestSubmit();
  });

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
  document.body.addEventListener('htmx:beforeRequest', ev => {
    if (isHeavy(ev.detail.elt)) overlay.classList.add('active');
  });
  document.body.addEventListener('htmx:afterRequest', ev => {
    if (isHeavy(ev.detail.elt)) overlay.classList.remove('active');
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
});
"""

# ═══════════════════════════════════════════════════════════════════════════
# App + State
# ═══════════════════════════════════════════════════════════════════════════

app = FastHTML(
    hdrs=(Style(CSS), htmxsrc, Script(JS)),
    default_hdrs=False,
)
rt = app.route

S = dict(
    df=None, all_dfs={}, sheets=[], sheet="",
    filename="", cols=[], tc="", sc="",
    dc=[], flt={}, ft={}, search="", sel=None,
)

TH = 50  # unique values <= this → multi-select chips
MAX_ROWS = 500  # cap rows rendered to browser (DOM weight)
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def sv(v):
    return "" if pd.isna(v) else str(v)

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
            style="border:1px solid var(--border);border-radius:var(--r);padding:14px;text-align:center;background:rgba(0,0,0,.15);",
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
            style="border:1px solid var(--border);border-radius:var(--r);padding:14px;text-align:center;background:rgba(0,0,0,.15);",
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
    return Div(sect("Detail Columns",
        Form(
            Div(
                Button("All", cls="btn bxs", data_sel="", type="button"),
                Button("Clear", cls="btn bxs", data_clear="", type="button"),
                style="display:flex;gap:3px;margin-bottom:4px;",
            ),
            Div(*chips, cls="fchips"),
            Input(type="hidden", name="dc_present", value="1"),
            Button("Apply", cls="btn bxs bp wf mt4"),
            hx_post="/cfg/detail-cols", hx_target="#detail",
        ),
    ), id="detail-pick")

def col_filters():
    if S["df"] is None or not S["cols"]: return Div()
    gs = []
    for col in S["cols"]:
        if col == S["tc"] or col == S["sc"]: continue
        n = int(S["df"][col].dropna().nunique())
        cv = S["flt"].get(col, set())
        ct = S["ft"].get(col, "")
        if n <= TH:
            vals = sorted(S["df"][col].dropna().unique()[:100], key=lambda x: str(x))
            chips = [Label(
                Input(type="checkbox", name=f"f_{col}", value=str(v), checked=(str(v) in cv)),
                str(v), cls=f"chip{' on' if str(v) in cv else ''}"
            ) for v in vals]
            gs.append(Div(
                Span(f"Filter: {col}", cls="fgrp-t"),
                Form(
                    Div(Button("All", cls="btn bxs", data_sel="", type="button"),
                        Button("Clear", cls="btn bxs", data_clear="", type="button"),
                        style="display:flex;gap:3px;margin-bottom:3px;"),
                    Div(*chips, cls="fchips"),
                    Input(type="hidden", name=f"f_{col}_present", value="1"),
                    Button("Apply", cls="btn bxs bp wf mt4"),
                    hx_post="/apply", hx_target="#main-wrap", hx_swap="outerHTML",
                    hx_include="#filter-form", data_autosubmit="true",
                ),
                cls="fgrp",
            ))
        else:
            gs.append(Div(
                Span(f"Filter: {col}", cls="fgrp-t"),
                Input(type="text", name=f"ft_{col}", placeholder=f"Filter {col}\u2026",
                      value=ct, hx_post="/apply", hx_target="#main-wrap",
                      hx_swap="outerHTML", hx_trigger="input changed delay:250ms",
                      hx_include="#filter-form", style="margin-top:3px;"),
                cls="fgrp",
            ))
    return Div(*gs)

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
        H4(f"Row {row_i + 1}", style="font-size:13px;font-weight:600;margin-bottom:10px;color:var(--accent)"),
        Div(*cells, cls="dgrid"),
    )

# ═══════════════════════════════════════════════════════════════════════════
# Layout
# ═══════════════════════════════════════════════════════════════════════════

def layout(f=None):
    if f is None: f = filt()
    sync_selection(f)
    total = len(S["df"]) if S["df"] is not None else 0
    cnt = len(f)
    return Div(
        # ── Left: Sidebar ─────────────────────────────────────────────
        Div(
            Div(Span("Excel Viewer", cls="stitle"),
                P(S["sheet"], cls="ssub") if S["sheet"] else Div(),
                cls="pnh"),
            Div(
                upload(), sheets(), title_pick(), sub_pick(), search_box(),
                detail_pick(),
                Div(
                    Label("Column Filters", cls="slbl"),
                    Div(col_filters(), id="col-filters", style="overflow-y:auto;flex:1;padding-top:6px;"),
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

@rt("/upload", methods=["POST"])
def post(file: File):
    data = file.file.read()
    file.file.close()  # release the spooled temp file promptly
    if len(data) > MAX_FILE_SIZE:
        S["error"] = f"File too large ({len(data)//(1024*1024)}MB). Max {MAX_FILE_SIZE//(1024*1024)}MB."
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
    S["dc"] = S["cols"][:]  # Initialize with all columns
    S["flt"] = {}; S["ft"] = {}; S["search"] = ""; S["sel"] = None
    return layout()

@rt("/close", methods=["POST"])
def post():
    for k in ("df","all_dfs","sheets","sheet","filename","cols","tc","sc","dc","flt","ft","search","sel","error"):
        S[k] = {} if k in ("all_dfs","flt","ft") else [] if k in ("sheets","cols","dc") \
              else "" if k in ("sheet","filename","tc","sc","search","error") else None
    return layout()

@rt("/clear-error", methods=["POST"])
def post():
    """Dismiss an upload error while keeping the currently loaded file."""
    S["error"] = None
    return layout()

@rt("/sheet", methods=["POST"])
def post(s: str):
    if s not in S["all_dfs"]: return Div("Invalid.", cls="empty", id="main-wrap")
    S["sheet"] = s
    S["df"] = S["all_dfs"][s]
    S["cols"] = list(S["df"].columns)
    S["tc"] = S["cols"][0] if S["cols"] else ""
    S["sc"] = S["cols"][1] if len(S["cols"]) > 1 else ""
    S["dc"] = S["cols"][:]  # Initialize with all columns
    S["flt"] = {}; S["ft"] = {}; S["search"] = ""; S["sel"] = None
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
            Div(col_filters(), id="col-filters", hx_swap_oob="true"))

@rt("/cfg/detail-cols", methods=["POST"])
async def post(req: Request):
    """Update detail columns without replacing entire app."""
    form = await req.form()
    dc_present = form.get("dc_present")
    if dc_present is not None:
        vals = form.getlist("dc")  # Get ALL checked checkboxes
        S["dc"] = [c for c in vals if c in S["cols"]]
    return detail_view(S["sel"])

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


# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)