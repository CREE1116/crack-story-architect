#!/usr/bin/env python3
"""대화형 웹 기반 스프라이트 누끼 터치업 스튜디오 (Sprite Touch-up Editor).

배경 위에서 실시간으로 스프라이트를 확인하며:
1. 지우개 (E): 불필요한 AI 모션라인, 후광, 아티팩트를 실시간 지움
2. 복원 브러시 (R): 깎여나간 끈이나 머리카락을 원본(raw) 이미지에서 자연스럽게 복구
3. 손도구 (H / Space / 마우스 우클릭 드래그): 캔버스 자유 이동 및 휠 줌
4. 배경 실시간 오버레이 검사 (체크판, 블랙, 화이트, 프로젝트 배경들)
5. 수정본을 즉시 `.cutouts_matte_cache/`에 저장 (Ctrl/Cmd+S)
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import unicodedata
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import cv2
import numpy as np


def nfc(t: str) -> str:
    return unicodedata.normalize('NFC', t)


HTML_CONTENT = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>스프라이트 누끼 정밀 터치업 스튜디오</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #121316; color: #e4e7eb; display: flex; height: 100vh; overflow: hidden; }
  
  /* Sidebar */
  #sidebar { width: 320px; background: #1a1c23; border-right: 1px solid #2d3139; display: flex; flex-direction: column; z-index: 10; }
  .side-header { padding: 16px; border-bottom: 1px solid #2d3139; }
  .side-header h1 { font-size: 16px; font-weight: 700; color: #fff; margin-bottom: 6px; }
  .side-header p { font-size: 12px; color: #8e95a5; }
  
  .side-body { flex: 1; overflow-y: auto; padding: 14px; }
  .control-group { margin-bottom: 16px; }
  .control-group label { display: block; font-size: 12px; font-weight: 600; color: #a6b0c3; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
  select, input[type="range"], button { width: 100%; border-radius: 6px; border: 1px solid #363b47; background: #222631; color: #fff; padding: 8px 10px; font-size: 13px; outline: none; }
  select:focus, button:hover { border-color: #6366f1; }
  
  .tool-row { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px; }
  .tool-btn { cursor: pointer; padding: 10px; font-weight: 600; border: 1px solid #363b47; background: #222631; border-radius: 6px; text-align: center; transition: all 0.15s; }
  .tool-btn.active { background: #4f46e5; border-color: #6366f1; color: #fff; box-shadow: 0 0 10px rgba(99, 102, 241, 0.4); }
  
  .bg-btn-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-top: 6px; }
  .bg-btn { cursor: pointer; font-size: 11px; padding: 6px; border: 1px solid #363b47; background: #222631; border-radius: 4px; text-align: center; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .bg-btn.active { border-color: #38bdf8; background: #0284c7; color: #fff; font-weight: bold; }

  .status-bar { padding: 12px 16px; border-top: 1px solid #2d3139; font-size: 12px; color: #10b981; display: flex; justify-content: space-between; align-items: center; }
  .save-btn { background: #10b981; border: none; font-weight: 700; color: #000; cursor: pointer; padding: 10px; border-radius: 6px; }
  .save-btn:hover { background: #059669; color: #fff; }

  /* Workspace Viewport */
  #workspace { flex: 1; position: relative; background: #0b0c0e; display: flex; align-items: center; justify-content: center; overflow: hidden; cursor: default; }
  #canvas-container { position: absolute; transform-origin: 0 0; box-shadow: 0 20px 50px rgba(0,0,0,0.8); }
  canvas { display: block; }
  #bg-canvas { position: absolute; top: 0; left: 0; z-index: 1; }
  #sprite-canvas { position: absolute; top: 0; left: 0; z-index: 2; }
  #cursor-canvas { position: absolute; top: 0; left: 0; z-index: 3; pointer-events: none; }

  /* Floating UI */
  .zoom-controls { position: absolute; top: 16px; right: 20px; display: flex; gap: 8px; z-index: 10; }
  .zoom-btn { background: rgba(26, 28, 35, 0.85); backdrop-filter: blur(8px); border: 1px solid #363b47; color: #fff; padding: 6px 12px; border-radius: 6px; font-size: 12px; cursor: pointer; }
  .zoom-btn:hover { background: #313644; }
  .zoom-overlay { background: rgba(0,0,0,0.7); backdrop-filter: blur(8px); padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; color: #38bdf8; border: 1px solid rgba(255,255,255,0.1); pointer-events: none; }

  .shortcuts { font-size: 11px; color: #64748b; line-height: 1.6; margin-top: 12px; border-top: 1px dashed #2d3139; padding-top: 10px; }
  .highlight { color: #38bdf8; font-weight: bold; }
</style>
</head>
<body>

<div id="sidebar">
  <div class="side-header">
    <h1>🎨 누끼 정밀 터치업 스튜디오</h1>
    <p>배경 위에서 실시간 지우개 / 복원 브러시로 수정</p>
  </div>

  <div class="side-body">
    <div class="control-group">
      <label>1. 캐릭터 선택</label>
      <select id="char-select"></select>
    </div>

    <div class="control-group">
      <label>2. 스프라이트 선택</label>
      <select id="sprite-select"></select>
    </div>

    <div class="control-group">
      <label>3. 도구 선택</label>
      <div class="tool-row">
        <div class="tool-btn active" id="tool-erase" onclick="setTool('erase')">🧹 지우개 (E)</div>
        <div class="tool-btn" id="tool-restore" onclick="setTool('restore')">🖌️ 복원 (R)</div>
      </div>
      <div class="tool-row">
        <div class="tool-btn" id="tool-hand" onclick="setTool('hand')">✋ 손도구 (H/Space)</div>
        <div class="tool-btn" id="tool-fit" onclick="fitToScreen()">🎯 화면 맞춤 (F)</div>
      </div>
      <div class="tool-row">
        <div class="tool-btn" id="tool-undo" onclick="undo()">↩️ 실행취소 (Ctrl+Z)</div>
        <div class="tool-btn" id="tool-reset" onclick="resetCurrent()">🔄 초기화</div>
      </div>
    </div>

    <div class="control-group">
      <label>브러시 크기: <span id="brush-size-val">15</span>px ( [ / ] )</label>
      <input type="range" id="brush-size" min="1" max="100" value="15" oninput="updateBrushSize(this.value)">
    </div>

    <div class="control-group">
      <label>브러시 부드러움: <span id="brush-soft-val">50</span>%</label>
      <input type="range" id="brush-soft" min="0" max="100" value="50" oninput="document.getElementById('brush-soft-val').innerText=this.value">
    </div>

    <div class="control-group">
      <label>4. 얹어볼 배경 선택 (검사 모드)</label>
      <div id="bg-container" class="bg-btn-grid"></div>
    </div>

    <div class="control-group" style="margin-top: 20px;">
      <button class="save-btn" onclick="saveToDisk()">💾 수정본 저장하기 (Ctrl/Cmd+S)</button>
    </div>

    <div class="shortcuts">
      <b>💡 조작 단축키:</b><br>
      • <span class="highlight">우클릭 드래그</span>: 언제든지 화면 이동(Pan)<br>
      • <span class="highlight">Space + 좌클릭</span>: 포토샵 스타일 이동<br>
      • <span class="highlight">E / R / H</span>: 지우개 / 복원 / 손도구 전환<br>
      • <span class="highlight">[ / ]</span>: 브러시 크기 조절<br>
      • <b>마우스 휠</b>: 캔버스 확대/축소 (Zoom)
    </div>
  </div>

  <div class="status-bar">
    <span id="status-text">준비 완료</span>
    <span id="res-text">0 × 0</span>
  </div>
</div>

<div id="workspace">
  <div class="zoom-controls">
    <button class="zoom-btn" onclick="zoomDelta(-0.2)">➖ 축소</button>
    <div class="zoom-overlay" id="zoom-badge">100%</div>
    <button class="zoom-btn" onclick="zoomDelta(0.2)">➕ 확대</button>
    <button class="zoom-btn" onclick="fitToScreen()">화면맞춤</button>
  </div>
  <div id="canvas-container">
    <canvas id="bg-canvas"></canvas>
    <canvas id="sprite-canvas"></canvas>
    <canvas id="cursor-canvas"></canvas>
  </div>
</div>

<script>
let currentTool = 'erase';
let brushSize = 15;
let currentBg = 'checker';
let scale = 1.0;
let panX = 0, panY = 0;
let isPanning = false, isDrawing = false;
let startMouseX = 0, startMouseY = 0;
let startPanX = 0, startPanY = 0;
let spacePressed = false;

let curWidth = 1216, curHeight = 832;

const workspace = document.getElementById('workspace');
const container = document.getElementById('canvas-container');
const bgCanvas = document.getElementById('bg-canvas');
const bgCtx = bgCanvas.getContext('2d');
const spriteCanvas = document.getElementById('sprite-canvas');
const spriteCtx = spriteCanvas.getContext('2d');
const cursorCanvas = document.getElementById('cursor-canvas');
const cursorCtx = cursorCanvas.getContext('2d');

let rawImg = new Image();
let pristineImg = new Image();
let undoStack = [];
let availableBgs = [];

async function init() {
  const res = await fetch('/api/config');
  const data = await res.json();
  
  const charSelect = document.getElementById('char-select');
  charSelect.innerHTML = data.characters.map(c => `<option value="${c}">${c}</option>`).join('');
  
  availableBgs = data.backgrounds || [];
  renderBgButtons();

  charSelect.onchange = () => loadSpriteList(charSelect.value);
  document.getElementById('sprite-select').onchange = () => loadCurrentSprite();
  
  if (data.characters.length > 0) {
    charSelect.value = data.characters[0];
    await loadSpriteList(data.characters[0]);
    await loadCurrentSprite();
    setTimeout(fitToScreen, 150);
  }
}

function renderBgButtons() {
  const bgBox = document.getElementById('bg-container');
  let html = `
    <div class="bg-btn active" onclick="setBg('checker')">체크판</div>
    <div class="bg-btn" onclick="setBg('black')">검정</div>
    <div class="bg-btn" onclick="setBg('white')">흰색</div>
  `;
  for (const bg of availableBgs) {
    html += `<div class="bg-btn" title="${bg}" onclick="setBg('${bg}')">${bg}</div>`;
  }
  bgBox.innerHTML = html;
}

async function loadSpriteList(char) {
  const res = await fetch(`/api/sprites?char=${encodeURIComponent(char)}`);
  const data = await res.json();
  const select = document.getElementById('sprite-select');
  select.innerHTML = data.sprites.map(s => `<option value="${s}">${s}</option>`).join('');
  if (data.sprites.length > 0) {
    select.value = data.sprites[0];
  }
}

async function loadCurrentSprite() {
  const char = document.getElementById('char-select').value;
  const sprite = document.getElementById('sprite-select').value;
  if (!char || !sprite) return;

  setStatus(`로딩 중: ${char} / ${sprite}...`);
  
  rawImg = new Image();
  rawImg.src = `/api/raw?char=${encodeURIComponent(char)}&sprite=${encodeURIComponent(sprite)}&t=${Date.now()}`;
  
  pristineImg = new Image();
  pristineImg.src = `/api/pristine?char=${encodeURIComponent(char)}&sprite=${encodeURIComponent(sprite)}&t=${Date.now()}`;
  
  await new Promise(r => {
    pristineImg.onload = r;
    pristineImg.onerror = r;
  });

  if (pristineImg.width > 0) {
    curWidth = pristineImg.width;
    curHeight = pristineImg.height;
  }
  
  resizeCanvases(curWidth, curHeight);
  document.getElementById('res-text').innerText = `${curWidth} × ${curHeight}`;

  spriteCtx.clearRect(0, 0, curWidth, curHeight);
  if (pristineImg.width > 0) {
    spriteCtx.drawImage(pristineImg, 0, 0);
  }
  undoStack = [];
  pushUndo();
  
  drawBackground();
  setStatus('준비 완료');
}

function resizeCanvases(w, h) {
  for (const c of [bgCanvas, spriteCanvas, cursorCanvas]) {
    c.width = w;
    c.height = h;
  }
  container.style.width = w + 'px';
  container.style.height = h + 'px';
}

function setTool(tool) {
  currentTool = tool;
  document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
  const btn = document.getElementById(`tool-${tool}`);
  if (btn) btn.classList.add('active');
  workspace.style.cursor = tool === 'hand' ? 'grab' : 'crosshair';
}

function updateBrushSize(val) {
  brushSize = parseInt(val);
  document.getElementById('brush-size-val').innerText = val;
}

function setBg(bgName) {
  currentBg = bgName;
  document.querySelectorAll('.bg-btn').forEach(b => {
    b.classList.toggle('active', b.innerText === bgName || (bgName === 'checker' && b.innerText === '체크판') || (bgName === 'black' && b.innerText === '검정') || (bgName === 'white' && b.innerText === '흰색'));
  });
  drawBackground();
}

function drawBackground() {
  bgCtx.clearRect(0, 0, curWidth, curHeight);
  if (currentBg === 'checker') {
    const size = 24;
    for (let y = 0; y < curHeight; y += size) {
      for (let x = 0; x < curWidth; x += size) {
        bgCtx.fillStyle = ((x / size + y / size) % 2 === 0) ? '#282c34' : '#1e2127';
        bgCtx.fillRect(x, y, size, size);
      }
    }
  } else if (currentBg === 'black') {
    bgCtx.fillStyle = '#050505';
    bgCtx.fillRect(0, 0, curWidth, curHeight);
  } else if (currentBg === 'white') {
    bgCtx.fillStyle = '#f8fafc';
    bgCtx.fillRect(0, 0, curWidth, curHeight);
  } else {
    const bgImg = new Image();
    bgImg.src = `/api/bg?name=${encodeURIComponent(currentBg)}&t=${Date.now()}`;
    bgImg.onload = () => {
      bgCtx.drawImage(bgImg, 0, 0, curWidth, curHeight);
    };
  }
}

function updateTransform() {
  container.style.transform = `translate(${panX}px, ${panY}px) scale(${scale})`;
  document.getElementById('zoom-badge').innerText = Math.round(scale * 100) + '%';
}

function zoomDelta(delta) {
  scale = Math.max(0.2, Math.min(5.0, scale + delta));
  updateTransform();
}

function fitToScreen() {
  const wsW = workspace.clientWidth - 40;
  const wsH = workspace.clientHeight - 40;
  scale = Math.min(wsW / curWidth, wsH / curHeight, 1.2);
  panX = (workspace.clientWidth - curWidth * scale) / 2;
  panY = (workspace.clientHeight - curHeight * scale) / 2;
  updateTransform();
}

function pushUndo() {
  if (undoStack.length > 20) undoStack.shift();
  undoStack.push(spriteCtx.getImageData(0, 0, curWidth, curHeight));
}

function undo() {
  if (undoStack.length > 1) {
    undoStack.pop();
    const prev = undoStack[undoStack.length - 1];
    spriteCtx.putImageData(prev, 0, 0);
    setStatus('실행 취소됨');
  }
}

function resetCurrent() {
  if (confirm('현재 수정한 내용을 모두 취소하고 처음 상태로 되돌릴까요?')) {
    spriteCtx.clearRect(0, 0, curWidth, curHeight);
    spriteCtx.drawImage(pristineImg, 0, 0);
    undoStack = [];
    pushUndo();
    setStatus('초기화 완료');
  }
}

// Drawing & Touch-up brush
function applyBrush(cx, cy) {
  const soft = parseInt(document.getElementById('brush-soft').value) / 100;
  
  spriteCtx.save();
  const rad = brushSize;
  const grad = spriteCtx.createRadialGradient(cx, cy, rad * (1 - soft), cx, cy, rad);
  
  if (currentTool === 'erase') {
    spriteCtx.globalCompositeOperation = 'destination-out';
    grad.addColorStop(0, 'rgba(0,0,0,1)');
    grad.addColorStop(1, 'rgba(0,0,0,0)');
    spriteCtx.fillStyle = grad;
    spriteCtx.beginPath();
    spriteCtx.arc(cx, cy, rad, 0, Math.PI * 2);
    spriteCtx.fill();
  } else if (currentTool === 'restore') {
    // Stamp from rawImg
    if (rawImg.width > 0) {
      const patternCanvas = document.createElement('canvas');
      patternCanvas.width = curWidth;
      patternCanvas.height = curHeight;
      const pctx = patternCanvas.getContext('2d');
      pctx.drawImage(rawImg, 0, 0, curWidth, curHeight);
      
      const pat = spriteCtx.createPattern(patternCanvas, 'no-repeat');
      spriteCtx.globalCompositeOperation = 'source-over';
      spriteCtx.fillStyle = pat;
      spriteCtx.beginPath();
      spriteCtx.arc(cx, cy, rad, 0, Math.PI * 2);
      spriteCtx.fill();
    }
  }
  spriteCtx.restore();
}

function drawCursor(cx, cy) {
  cursorCtx.clearRect(0, 0, curWidth, curHeight);
  if (currentTool === 'hand') return;
  cursorCtx.beginPath();
  cursorCtx.arc(cx, cy, brushSize, 0, Math.PI * 2);
  cursorCtx.strokeStyle = currentTool === 'erase' ? 'rgba(239, 68, 68, 0.9)' : 'rgba(16, 185, 129, 0.9)';
  cursorCtx.lineWidth = 1.5 / scale;
  cursorCtx.stroke();
}

function getCanvasPos(e) {
  const rect = container.getBoundingClientRect();
  return {
    x: (e.clientX - rect.left) / scale,
    y: (e.clientY - rect.top) / scale
  };
}

workspace.addEventListener('mousedown', (e) => {
  if (e.button === 2 || currentTool === 'hand' || spacePressed) {
    isPanning = true;
    startMouseX = e.clientX;
    startMouseY = e.clientY;
    startPanX = panX;
    startPanY = panY;
    workspace.style.cursor = 'grabbing';
    e.preventDefault();
    return;
  }
  
  if (e.button === 0 && (currentTool === 'erase' || currentTool === 'restore')) {
    isDrawing = true;
    const pos = getCanvasPos(e);
    applyBrush(pos.x, pos.y);
    drawCursor(pos.x, pos.y);
  }
});

window.addEventListener('mousemove', (e) => {
  if (isPanning) {
    panX = startPanX + (e.clientX - startMouseX);
    panY = startPanY + (e.clientY - startMouseY);
    updateTransform();
    return;
  }
  
  const pos = getCanvasPos(e);
  if (isDrawing) {
    applyBrush(pos.x, pos.y);
  }
  drawCursor(pos.x, pos.y);
});

window.addEventListener('mouseup', (e) => {
  if (isPanning) {
    isPanning = false;
    workspace.style.cursor = currentTool === 'hand' ? 'grab' : 'crosshair';
  }
  if (isDrawing) {
    isDrawing = false;
    pushUndo();
  }
});

workspace.addEventListener('contextmenu', e => e.preventDefault());

workspace.addEventListener('wheel', (e) => {
  e.preventDefault();
  const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
  const newScale = Math.max(0.2, Math.min(5.0, scale * zoomFactor));
  
  const rect = workspace.getBoundingClientRect();
  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;
  
  panX = mouseX - (mouseX - panX) * (newScale / scale);
  panY = mouseY - (mouseY - panY) * (newScale / scale);
  scale = newScale;
  updateTransform();
}, { passive: false });

window.addEventListener('keydown', (e) => {
  if (e.code === 'Space') {
    spacePressed = true;
    workspace.style.cursor = 'grab';
  } else if (e.key === 'e' || e.key === 'E') {
    setTool('erase');
  } else if (e.key === 'r' || e.key === 'R') {
    setTool('restore');
  } else if (e.key === 'h' || e.key === 'H') {
    setTool('hand');
  } else if (e.key === 'f' || e.key === 'F') {
    fitToScreen();
  } else if (e.key === '[') {
    updateBrushSize(Math.max(1, brushSize - 5));
    document.getElementById('brush-size').value = brushSize;
  } else if (e.key === ']') {
    updateBrushSize(Math.min(100, brushSize + 5));
    document.getElementById('brush-size').value = brushSize;
  } else if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
    e.preventDefault();
    undo();
  } else if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault();
    saveToDisk();
  }
});

window.addEventListener('keyup', (e) => {
  if (e.code === 'Space') {
    spacePressed = false;
    workspace.style.cursor = currentTool === 'hand' ? 'grab' : 'crosshair';
  }
});

async function saveToDisk() {
  const char = document.getElementById('char-select').value;
  const sprite = document.getElementById('sprite-select').value;
  setStatus(`저장 중: ${char}/${sprite}...`);
  
  const dataUrl = spriteCanvas.toDataURL('image/png');
  const res = await fetch('/api/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ char, sprite, data: dataUrl })
  });
  
  const result = await res.json();
  if (result.ok) {
    setStatus(`✅ 저장 성공! (${result.saved_path})`);
  } else {
    setStatus(`❌ 저장 실패: ${result.error}`);
  }
}

function setStatus(text) {
  document.getElementById('status-text').innerText = text;
}

window.onload = init;
</script>
</body>
</html>
"""

_EDITOR_CFG = {}


class TouchupServer(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        cfg = _EDITOR_CFG
        img_dir = cfg['img_dir']
        bg_dir = cfg['bg_dir']
        cache_dir = cfg['cache_dir']

        if parsed.path in ('/', '/index.html'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode('utf-8'))
            return

        if parsed.path == '/api/config':
            # Scan characters & backgrounds
            chars = []
            if img_dir.exists():
                for p in sorted(img_dir.iterdir()):
                    if p.is_dir() and not p.name.startswith('.'):
                        chars.append(nfc(p.name))
            bgs = []
            if bg_dir.exists():
                for p in sorted(bg_dir.iterdir()):
                    if not p.name.startswith('.') and p.suffix.lower() in ('.png', '.jpg', '.webp'):
                        bgs.append(nfc(p.stem))
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'characters': chars, 'backgrounds': bgs}).encode('utf-8'))
            return

        if parsed.path == '/api/sprites':
            char = qs.get('char', [''])[0]
            sprite_dir = cache_dir / char
            if not sprite_dir.exists():
                # fallback to img_dir / char / '검정'
                sprite_dir = img_dir / char / '검정'
            if not sprite_dir.exists():
                sprite_dir = img_dir / char
            sprites = [f.name for f in sorted(sprite_dir.glob('*.png')) if not f.name.startswith('.')] if sprite_dir.exists() else []
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'sprites': sprites}).encode('utf-8'))
            return

        if parsed.path == '/api/raw':
            char = qs.get('char', [''])[0]
            sprite = qs.get('sprite', [''])[0]
            raw_path = img_dir / char / '검정' / nfc(sprite)
            if not raw_path.exists():
                raw_path = img_dir / char / nfc(sprite)
            if not raw_path.exists():
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            with open(raw_path, 'rb') as f:
                self.wfile.write(f.read())
            return

        if parsed.path == '/api/pristine':
            char = qs.get('char', [''])[0]
            sprite = qs.get('sprite', [''])[0]
            pristine_path = cache_dir / char / nfc(sprite)
            if not pristine_path.exists():
                # fallback to raw
                pristine_path = img_dir / char / '검정' / nfc(sprite)
            if not pristine_path.exists():
                pristine_path = img_dir / char / nfc(sprite)
            if not pristine_path.exists():
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            with open(pristine_path, 'rb') as f:
                self.wfile.write(f.read())
            return

        if parsed.path == '/api/bg':
            name = qs.get('name', [''])[0]
            found = None
            if bg_dir.exists():
                for ext in ('.png', '.jpg', '.webp'):
                    candidate = bg_dir / f'{name}{ext}'
                    if candidate.exists():
                        found = candidate
                        break
            if not found:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            with open(found, 'rb') as f:
                self.wfile.write(f.read())
            return

        self.send_error(404)

    def do_POST(self):
        if self.path == '/api/save':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            payload = json.loads(body.decode('utf-8'))
            char = payload.get('char')
            sprite = payload.get('sprite')
            data_url = payload.get('data')

            if ',' in data_url:
                _, encoded = data_url.split(',', 1)
                img_bytes = base64.b64decode(encoded)
                cache_dir = _EDITOR_CFG['cache_dir']
                target_path = cache_dir / char / nfc(sprite)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with open(target_path, 'wb') as f:
                    f.write(img_bytes)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'ok': True, 'saved_path': str(target_path.name)}).encode('utf-8'))
                return

        self.send_error(400)


def main():
    parser = argparse.ArgumentParser(description='스프라이트 누끼 정밀 터치업 스튜디오 (웹 UI)')
    parser.add_argument('--project', default='.', help='프로젝트 루트 경로 (기본: 현재 폴더)')
    parser.add_argument('--img-dir', help='스프라이트 폴더 (기본: <project>/img)')
    parser.add_argument('--bg-dir', help='배경 폴더 (기본: <project>/배경)')
    parser.add_argument('--cache-dir', help='누끼 캐시 폴더 (기본: <img-dir>/.cutouts_matte_cache)')
    parser.add_argument('--host', default='127.0.0.1', help='호스트 (기본: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8765, help='포트 (기본: 8765)')
    args = parser.parse_args()

    project_root = Path(args.project).resolve()
    img_dir = Path(args.img_dir) if args.img_dir else (project_root / 'img')
    bg_dir = Path(args.bg_dir) if args.bg_dir else (project_root / '배경')
    cache_dir = Path(args.cache_dir) if args.cache_dir else (img_dir / '.cutouts_matte_cache')

    global _EDITOR_CFG
    _EDITOR_CFG = {
        'project': project_root,
        'img_dir': img_dir,
        'bg_dir': bg_dir,
        'cache_dir': cache_dir,
    }

    server_address = (args.host, args.port)
    httpd = HTTPServer(server_address, TouchupServer)
    print(f'🚀 [스프라이트 터치업 스튜디오] 브라우저에서 실행 중:')
    print(f'   👉 http://{args.host}:{args.port}')
    print(f'   스프라이트: {img_dir}')
    print(f'   누끼 캐시: {cache_dir}')
    print(f'   배경 폴더: {bg_dir}')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n서버를 종료합니다.')


if __name__ == '__main__':
    main()
