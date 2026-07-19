#!/usr/bin/env python3
"""Generate a screenshot-only UIForge Visual Review gallery."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

GENERATOR_ID = "ui-forge.visual-review"
GENERATOR_VERSION = "1"


def load_manifest(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("manifest schema_version must be 1")
    screens = data.get("screens")
    if not isinstance(screens, list) or not screens:
        raise ValueError("manifest must contain at least one screen")
    required = {"screen_key", "name", "figma_node_id", "width", "height", "screenshot"}
    seen = set()
    for index, screen in enumerate(screens):
        missing = sorted(required - set(screen))
        if missing:
            raise ValueError(f"screen {index} missing: {', '.join(missing)}")
        key = screen["screen_key"]
        if key in seen:
            raise ValueError(f"duplicate screen_key: {key}")
        seen.add(key)
    return data


def render(manifest: dict) -> str:
    active = [s for s in manifest["screens"] if s.get("status") != "archived"]
    encoded = json.dumps(manifest, ensure_ascii=False).replace("</", "<\\/")
    buttons = []
    views = []
    for idx, screen in enumerate(active):
        status = html.escape(screen.get("status", "unchanged"))
        group = html.escape(screen.get("group", "Screens"))
        screen_key = str(screen["screen_key"])
        stable_id = re.sub(r"[^a-zA-Z0-9_-]+", "-", screen_key).strip("-") or f"screen-{idx}"
        active_class = " active" if idx == 0 else ""
        hidden = "" if idx == 0 else " hidden"
        buttons.append(
            f'<button class="screen-button{active_class}" data-index="{idx}">'
            f'<span><b>{html.escape(screen["name"])}</b><small>{group}</small></span>'
            f'<em class="status {status}">{status}</em></button>'
        )
        views.append(
            f'<figure class="screen-view{active_class}" data-index="{idx}" '
            f'id="view-{html.escape(stable_id)}"{hidden}>'
            f'<img id="shot-{html.escape(stable_id)}" class="shot" '
            f'src="{html.escape(screen["screenshot"])}" alt="{html.escape(screen["name"])}">'
            f"</figure>"
        )
    first = active[0]
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="generator" content="{GENERATOR_ID}@{GENERATOR_VERSION}">
<title>UIForge Visual Review</title><style>
:root{{--bg:#111116;--panel:#1c1c23;--line:#30303b;--text:#f7f7fb;--muted:#9b9baa;--violet:#7c3aed;--lime:#c3f80a}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:14px/1.5 Inter,system-ui,sans-serif;height:100vh;overflow:hidden}}
.app{{display:grid;grid-template-columns:300px 1fr;height:100%}}aside{{background:var(--panel);border-right:1px solid var(--line);padding:20px;overflow:auto}}
h1{{font-size:20px;margin:0 0 4px}}.summary{{color:var(--muted);margin-bottom:16px}}
.screen-button{{width:100%;display:flex;align-items:center;justify-content:space-between;text-align:left;color:var(--text);background:transparent;border:1px solid transparent;border-radius:12px;padding:10px;margin:4px 0;cursor:pointer}}
.screen-button:hover,.screen-button.active{{background:#292934;border-color:#3d3d49}}.screen-button span{{display:flex;flex-direction:column}}small{{color:var(--muted)}}em{{font-style:normal;font-size:10px;padding:3px 7px;border-radius:999px;background:#353541}}em.new{{background:#31410a;color:var(--lime)}}em.changed{{background:#41213a;color:#ff7baa}}
main{{display:grid;grid-template-rows:auto 1fr;min-width:0}}header{{display:flex;justify-content:space-between;align-items:center;padding:18px 24px;border-bottom:1px solid var(--line)}}header h2{{margin:0;font-size:18px}}header p{{margin:2px 0 0;color:var(--muted)}}.node{{font:12px ui-monospace,monospace;color:var(--lime)}}
.canvas{{overflow:auto;padding:32px;background:radial-gradient(circle at 50% 0,#242033 0,transparent 42%)}}.screen-view{{display:none;margin:0 auto;width:max-content;max-width:100%}}.screen-view.active{{display:block}}.shot{{max-width:min(100%,720px);height:auto;display:block;border-radius:18px;box-shadow:0 24px 80px #0008;background:white}}
.help{{width:max-content;max-width:100%;margin:48px auto 0;background:#202027;border:1px solid var(--line);color:var(--muted);border-radius:12px;padding:10px 14px;text-align:center}}
</style></head><body>
<div class="app" data-ui-forge-generator="{GENERATOR_VERSION}"><aside><h1>Visual Review</h1><div class="summary">{len(active)} 个 Figma 页面</div><div id="screens">{''.join(buttons)}</div></aside>
<main><header><div><h2 id="title">{html.escape(first["name"])}</h2><p id="group">{html.escape(first.get("group", "Screens"))}</p></div><div class="node" id="node">Figma {html.escape(first["figma_node_id"])}</div></header>
<div class="canvas">{''.join(views)}<div class="help">直接使用 Codex 标注功能圈选截图并留言；修改会同步回 Figma。</div></div></main></div>
<script id="manifest" type="application/json">{encoded}</script><script>
const manifest=JSON.parse(document.getElementById('manifest').textContent);const screens=manifest.screens.filter(s=>s.status!=='archived');
const buttons=[...document.querySelectorAll('.screen-button')],views=[...document.querySelectorAll('.screen-view')];const title=document.getElementById('title'),group=document.getElementById('group'),node=document.getElementById('node');
function select(i){{const s=screens[i];buttons.forEach((b,j)=>b.classList.toggle('active',i===j));views.forEach((v,j)=>{{const active=i===j;v.classList.toggle('active',active);v.hidden=!active;}});title.textContent=s.name;group.textContent=s.group||'Screens';node.textContent='Figma '+s.figma_node_id;history.replaceState(null,'','#'+encodeURIComponent(s.screen_key));}}
buttons.forEach((b,i)=>b.onclick=()=>select(i));
const hash=decodeURIComponent(location.hash.slice(1));select(Math.max(0,screens.findIndex(s=>s.screen_key===hash)));
</script></body></html>'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(manifest), encoding="utf-8")
    count = sum(s.get("status") != "archived" for s in manifest["screens"])
    print(f"wrote {args.output} with {count} screens")


if __name__ == "__main__":
    main()
