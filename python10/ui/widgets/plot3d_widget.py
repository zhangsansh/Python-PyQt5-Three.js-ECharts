# -*- coding: utf-8 -*-
"""基于 Three.js 的精美可交互 3D 建模（点击查看样本信息）"""
import json
import os

import numpy as np
from PyQt5.QtCore import Qt, QUrl, QTimer, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from ui.styles import FONT_6

RISK_NAMES = {0: "低风险", 1: "中风险", 2: "高风险"}


def _build_html(title, points, labels, infos=None, empty=False, stage=""):
    data = {
        "points": points,
        "labels": labels,
        "infos": infos or [],
        "empty": empty,
        "title": title,
        "stage": stage or title,
    }
    payload = json.dumps(data, ensure_ascii=False)
    # 双大括号转义 CSS/JS 中的 { }
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  html,body{{margin:0;padding:0;width:100%;height:100%;overflow:hidden;background:#060e1a;
    font-family:"Microsoft YaHei","Segoe UI",sans-serif;}}
  #c{{width:100%;height:100%;display:block;cursor:crosshair;}}
  #hud{{position:absolute;left:8px;top:6px;color:#9ad0ff;font-size:11px;
        text-shadow:0 1px 4px #000;z-index:3;pointer-events:none;line-height:1.4;}}
  #legend{{position:absolute;right:8px;top:6px;color:#dceeff;font-size:11px;
        background:rgba(6,18,36,0.82);padding:8px 10px;border-radius:8px;
        border:1px solid rgba(94,200,255,0.35);backdrop-filter:blur(6px);z-index:3;}}
  #legend span{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px;
        vertical-align:middle;box-shadow:0 0 6px currentColor;}}
  #info{{
    position:absolute;left:10px;bottom:10px;width:min(320px,88%);max-height:46%;
    overflow:auto;z-index:4;display:none;
    background:linear-gradient(160deg,rgba(10,28,52,0.95),rgba(8,40,70,0.92));
    border:1px solid rgba(94,200,255,0.5);border-radius:10px;padding:10px 12px;
    color:#e8f4ff;box-shadow:0 8px 28px rgba(0,0,0,0.45),0 0 18px rgba(30,144,255,0.2);
    animation:popIn .28s ease-out;
  }}
  #info.show{{display:block;}}
  #info h4{{margin:0 0 6px 0;color:#5ec8ff;font-size:13px;}}
  #info .tag{{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;margin-bottom:6px;}}
  #info .tag.r0{{background:rgba(0,229,160,.2);color:#00e5a0;border:1px solid #00e5a0;}}
  #info .tag.r1{{background:rgba(255,193,7,.2);color:#ffc107;border:1px solid #ffc107;}}
  #info .tag.r2{{background:rgba(255,82,82,.2);color:#ff8a80;border:1px solid #ff5252;}}
  #info table{{width:100%;border-collapse:collapse;font-size:11px;}}
  #info td{{padding:3px 2px;border-bottom:1px solid rgba(42,90,138,.45);}}
  #info td.k{{color:#8ecfff;width:42%;}}
  #info td.v{{color:#fff;text-align:right;}}
  #closeInfo{{position:absolute;right:8px;top:6px;background:transparent;border:none;
    color:#8ecfff;cursor:pointer;font-size:14px;}}
  @keyframes popIn{{from{{opacity:0;transform:translateY(10px) scale(.96);}}
    to{{opacity:1;transform:translateY(0) scale(1);}}}}
  #flash{{position:absolute;inset:0;pointer-events:none;z-index:2;opacity:0;
    background:radial-gradient(circle at var(--x,50%) var(--y,50%),rgba(94,200,255,.35),transparent 42%);
    transition:opacity .15s;}}
</style>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
<div id="hud">精美建模 · 左键旋转 / 右键平移 / 滚轮缩放<br/>单击样本点查看详细数据</div>
<div id="legend">
  <div><span style="background:#00e5a0;color:#00e5a0"></span>低风险</div>
  <div><span style="background:#ffc107;color:#ffc107"></span>中风险</div>
  <div><span style="background:#ff5252;color:#ff5252"></span>高风险</div>
</div>
<div id="flash"></div>
<div id="info"><button id="closeInfo" title="关闭">✕</button><div id="infoBody"></div></div>
<canvas id="c"></canvas>
<script>
const DATA = {payload};
const canvas = document.getElementById('c');
const flashEl = document.getElementById('flash');
const infoEl = document.getElementById('info');
const infoBody = document.getElementById('infoBody');
document.getElementById('closeInfo').onclick = () => infoEl.classList.remove('show');

const renderer = new THREE.WebGLRenderer({{canvas: canvas, antialias: true, alpha: true, preserveDrawingBuffer: true}});
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setClearColor(0x060e1a, 1);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputEncoding = THREE.sRGBEncoding;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x060e1a, 0.028);

const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 200);
camera.position.set(5.2, 4.2, 6.2);

const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.07;
controls.screenSpacePanning = true;
controls.minDistance = 2;
controls.maxDistance = 28;
controls.target.set(0, 0.2, 0);
controls.rotateSpeed = 0.7;

// —— 灯光（更贴近现实）——
scene.add(new THREE.HemisphereLight(0xb8d4ff, 0x1a3048, 0.55));
const key = new THREE.DirectionalLight(0xffffff, 0.95);
key.position.set(6, 10, 4);
key.castShadow = true;
key.shadow.mapSize.set(1024, 1024);
key.shadow.camera.near = 1;
key.shadow.camera.far = 30;
key.shadow.camera.left = key.shadow.camera.bottom = -8;
key.shadow.camera.right = key.shadow.camera.top = 8;
scene.add(key);
const fill = new THREE.DirectionalLight(0x5ec8ff, 0.35);
fill.position.set(-5, 3, -3);
scene.add(fill);
const rim = new THREE.PointLight(0x1e90ff, 0.7, 30);
rim.position.set(0, 5, -6);
scene.add(rim);

// —— 地面与环境 ——
const ground = new THREE.Mesh(
  new THREE.CircleGeometry(9, 64),
  new THREE.MeshStandardMaterial({{
    color: 0x0b1c30, metalness: 0.55, roughness: 0.35,
    transparent: true, opacity: 0.92
  }})
);
ground.rotation.x = -Math.PI / 2;
ground.position.y = -3.6;
ground.receiveShadow = true;
scene.add(ground);

const grid = new THREE.GridHelper(12, 24, 0x3aa0ff, 0x16304a);
grid.position.y = -3.55;
grid.material.transparent = true;
grid.material.opacity = 0.35;
scene.add(grid);

// 半透明玻璃罩
const dome = new THREE.Mesh(
  new THREE.SphereGeometry(7.2, 48, 32, 0, Math.PI * 2, 0, Math.PI * 0.55),
  new THREE.MeshPhysicalMaterial({{
    color: 0x1e90ff, metalness: 0.1, roughness: 0.1, transparent: true,
    opacity: 0.06, side: THREE.DoubleSide, clearcoat: 1
  }})
);
dome.position.y = -0.5;
scene.add(dome);

const axes = new THREE.AxesHelper(2.4);
axes.position.set(-3.8, -3.4, -3.8);
scene.add(axes);

let meshRoot = new THREE.Group();
scene.add(meshRoot);
let pickMeshes = [];
let worldPositions = [];
let metaList = [];
let selectedMesh = null;
let pulseRing = null;
let pulseT = 0;

function disposeGroup(g) {{
  g.traverse(obj => {{
    if (obj.geometry) obj.geometry.dispose();
    if (obj.material) {{
      if (Array.isArray(obj.material)) obj.material.forEach(m => m.dispose());
      else obj.material.dispose();
    }}
  }});
  while (g.children.length) g.remove(g.children[0]);
}}

function riskColor(r) {{
  if (r === 1) return new THREE.Color(0xffc107);
  if (r === 2) return new THREE.Color(0xff5252);
  return new THREE.Color(0x00e5a0);
}}

function clearScenePoints() {{
  disposeGroup(meshRoot);
  pickMeshes = [];
  worldPositions = [];
  metaList = [];
  selectedMesh = null;
  if (pulseRing) {{ scene.remove(pulseRing); pulseRing.geometry.dispose(); pulseRing.material.dispose(); pulseRing = null; }}
}}

function makePulseRing() {{
  const geo = new THREE.RingGeometry(0.12, 0.2, 48);
  const mat = new THREE.MeshBasicMaterial({{
    color: 0x5ec8ff, transparent: true, opacity: 0.85, side: THREE.DoubleSide
  }});
  pulseRing = new THREE.Mesh(geo, mat);
  pulseRing.visible = false;
  scene.add(pulseRing);
}}
makePulseRing();

function plot(data) {{
  clearScenePoints();
  makePulseRing();
  if (data.empty || !data.points || !data.points.length) {{
    const ball = new THREE.Mesh(
      new THREE.SphereGeometry(0.45, 32, 32),
      new THREE.MeshStandardMaterial({{
        color: 0x2a5a8a, metalness: 0.6, roughness: 0.25, emissive: 0x0a2038, emissiveIntensity: 0.4
      }})
    );
    ball.castShadow = true;
    meshRoot.add(ball);
    return;
  }}
  const pts = data.points;
  const labs = data.labels;
  const infos = data.infos || [];
  const n = Math.min(pts.length, 500);
  let minX=Infinity,maxX=-Infinity,minY=Infinity,maxY=-Infinity,minZ=Infinity,maxZ=-Infinity;
  for (let i=0;i<n;i++) {{
    const p=pts[i];
    minX=Math.min(minX,p[0]); maxX=Math.max(maxX,p[0]);
    minY=Math.min(minY,p[1]); maxY=Math.max(maxY,p[1]);
    minZ=Math.min(minZ,p[2]); maxZ=Math.max(maxZ,p[2]);
  }}
  const sx=(maxX-minX)||1, sy=(maxY-minY)||1, sz=(maxZ-minZ)||1;

  const sphereGeo = new THREE.SphereGeometry(0.09, 16, 16);
  for (let i=0;i<n;i++) {{
    const p = pts[i];
    const x = ((p[0]-minX)/sx - 0.5) * 6.5;
    const y = ((p[1]-minY)/sy - 0.5) * 6.5;
    const z = ((p[2]-minZ)/sz - 0.5) * 6.5;
    const risk = labs[i]|0;
    const col = riskColor(risk);
    const mat = new THREE.MeshStandardMaterial({{
      color: col, metalness: 0.35, roughness: 0.28,
      emissive: col, emissiveIntensity: 0.22,
      transparent: true, opacity: 0.92
    }});
    const m = new THREE.Mesh(sphereGeo, mat);
    m.position.set(x, y, z);
    m.castShadow = true;
    m.receiveShadow = true;
    m.userData = {{ index: i, risk: risk }};
    meshRoot.add(m);
    pickMeshes.push(m);
    worldPositions.push(new THREE.Vector3(x,y,z));

    const info = infos[i] || {{
      id: i, risk: risk, risk_name: ['低风险','中风险','高风险'][risk] || String(risk),
      features: {{}}, pca: [p[0], p[1], p[2]]
    }};
    info.pca = [Number(p[0].toFixed ? p[0].toFixed(4) : p[0]),
                Number(p[1].toFixed ? p[1].toFixed(4) : p[1]),
                Number(p[2].toFixed ? p[2].toFixed(4) : p[2])];
    info.world = [x.toFixed(3), y.toFixed(3), z.toFixed(3)];
    info.stage = data.stage || data.title || '';
    metaList.push(info);

    // 细连接线到地面，增强空间感
    if (i % 7 === 0) {{
      const lineGeo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(x,y,z), new THREE.Vector3(x, -3.55, z)
      ]);
      const line = new THREE.Line(lineGeo, new THREE.LineBasicMaterial({{
        color: col, transparent: true, opacity: 0.12
      }}));
      meshRoot.add(line);
    }}
  }}
}}

const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();
raycaster.params.Points = {{ threshold: 0.2 }};

function showInfo(info, clientX, clientY) {{
  const risk = info.risk|0;
  let featRows = '';
  const feats = info.features || {{}};
  const keys = Object.keys(feats);
  if (keys.length) {{
    featRows = keys.map(k => `<tr><td class="k">${{k}}</td><td class="v">${{feats[k]}}</td></tr>`).join('');
  }} else {{
    featRows = `<tr><td class="k">PCA-X</td><td class="v">${{info.pca[0]}}</td></tr>
      <tr><td class="k">PCA-Y</td><td class="v">${{info.pca[1]}}</td></tr>
      <tr><td class="k">PCA-Z</td><td class="v">${{info.pca[2]}}</td></tr>`;
  }}
  let conf = '';
  if (info.confidence != null) {{
    conf = `<tr><td class="k">置信度</td><td class="v">${{(info.confidence*100).toFixed(2)}}%</td></tr>`;
  }}
  if (info.proba) {{
    conf += `<tr><td class="k">概率分布</td><td class="v">${{info.proba.map(v=>(v*100).toFixed(1)+'%').join(' / ')}}</td></tr>`;
  }}
  infoBody.innerHTML = `
    <h4>样本 #${{info.id}}</h4>
    <div class="tag r${{risk}}">${{info.risk_name || ''}}</div>
    <div style="font-size:11px;color:#9bb8d4;margin-bottom:6px;">${{info.stage || ''}}</div>
    <table>
      <tr><td class="k">三维坐标</td><td class="v">(${{(info.world||[]).join(', ')}})</td></tr>
      ${{conf}}
      ${{featRows}}
    </table>`;
  infoEl.classList.add('show');
  // 屏幕闪光特效
  const rect = canvas.getBoundingClientRect();
  flashEl.style.setProperty('--x', ((clientX-rect.left)/rect.width*100)+'%');
  flashEl.style.setProperty('--y', ((clientY-rect.top)/rect.height*100)+'%');
  flashEl.style.opacity = '1';
  setTimeout(() => flashEl.style.opacity = '0', 220);
}}

function onPointerDown(ev) {{
  if (ev.button !== 0) return;
  const rect = canvas.getBoundingClientRect();
  mouse.x = ((ev.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((ev.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);
  const hits = raycaster.intersectObjects(pickMeshes, false);
  if (!hits.length) {{
    infoEl.classList.remove('show');
    if (selectedMesh) {{ selectedMesh.scale.set(1,1,1); selectedMesh = null; }}
    if (pulseRing) pulseRing.visible = false;
    return;
  }}
  const hit = hits[0];
  const idx = hit.object.userData.index;
  const info = metaList[idx];
  if (selectedMesh && selectedMesh !== hit.object) selectedMesh.scale.set(1,1,1);
  selectedMesh = hit.object;
  selectedMesh.scale.set(1.85, 1.85, 1.85);
  pulseRing.position.copy(hit.object.position);
  pulseRing.visible = true;
  pulseT = 0;
  showInfo(info, ev.clientX, ev.clientY);
}}
canvas.addEventListener('pointerdown', onPointerDown);

function resize() {{
  const w = window.innerWidth || 400;
  const h = window.innerHeight || 300;
  renderer.setSize(w, h, false);
  camera.aspect = w / Math.max(h, 1);
  camera.updateProjectionMatrix();
}}
window.addEventListener('resize', resize);
resize();
plot(DATA);

let t = 0;
function animate() {{
  requestAnimationFrame(animate);
  t += 0.01;
  controls.update();
  // 环境微动
  rim.intensity = 0.55 + Math.sin(t * 1.3) * 0.15;
  meshRoot.rotation.y = Math.sin(t * 0.15) * 0.03;
  if (selectedMesh) {{
    const s = 1.7 + Math.sin(t * 6) * 0.15;
    selectedMesh.scale.set(s, s, s);
  }}
  if (pulseRing && pulseRing.visible) {{
    pulseT += 0.04;
    const sc = 1 + pulseT * 2.2;
    pulseRing.scale.set(sc, sc, 1);
    pulseRing.material.opacity = Math.max(0, 0.9 - pulseT * 0.55);
    pulseRing.rotation.x = Math.PI / 2;
    if (pulseT > 1.6) {{ pulseT = 0; }}
  }}
  renderer.render(scene, camera);
}}
animate();

window.updateScene = function(jsonStr) {{
  try {{
    const d = (typeof jsonStr === 'string') ? JSON.parse(jsonStr) : jsonStr;
    plot(d);
  }} catch (e) {{ console.error(e); }}
}};
</script>
</body>
</html>"""


class Plot3DWidget(QWidget):
    """Three.js 精美 3D 建模视图（支持点击查看样本）"""

    point_clicked = pyqtSignal(dict)

    def __init__(self, title="3D模型", parent=None):
        super().__init__(parent)
        self.title_text = title
        self._last_points = []
        self._last_labels = []
        self._last_infos = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(
            f"color:#5ec8ff;font-size:{FONT_6};font-weight:bold;background:transparent;"
        )
        layout.addWidget(self.title_label)

        self.view = QWebEngineView()
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.view.setMinimumHeight(180)
        settings = self.view.settings()
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
        layout.addWidget(self.view, 1)

        tip = QLabel("Three.js · 旋转/平移/缩放 · 单击样本查看数据（光效高亮）")
        tip.setAlignment(Qt.AlignCenter)
        tip.setStyleSheet(f"color:#6a8aaa;font-size:{FONT_6};background:transparent;")
        layout.addWidget(tip)

        self.show_empty()

    def set_title(self, title):
        self.title_text = title
        self.title_label.setText(title)

    def show_empty(self):
        html = _build_html(self.title_text, [], [], empty=True)
        self.view.setHtml(html, QUrl("https://cdn.jsdelivr.net/"))

    def plot_points(self, points, labels, title=None, max_points=500, infos=None, stage=""):
        if title:
            self.set_title(title)
        pts = np.asarray(points, dtype=float)
        labs = np.asarray(labels)
        info_list = list(infos) if infos is not None else []
        if pts.size == 0:
            self.show_empty()
            return
        if pts.ndim == 1:
            pts = pts.reshape(-1, 1)
        if pts.shape[1] < 3:
            pad = np.zeros((pts.shape[0], 3 - pts.shape[1]))
            pts = np.hstack([pts, pad])
        if len(pts) > max_points:
            idx = np.random.RandomState(0).choice(len(pts), max_points, replace=False)
            pts = pts[idx]
            labs = labs[idx]
            if info_list:
                info_list = [info_list[i] for i in idx if i < len(info_list)]

        self._last_points = pts.tolist()
        self._last_labels = [int(x) for x in labs.tolist()]
        # 补齐 infos
        while len(info_list) < len(self._last_labels):
            i = len(info_list)
            r = self._last_labels[i]
            info_list.append({
                "id": i,
                "risk": r,
                "risk_name": RISK_NAMES.get(r, str(r)),
                "features": {},
            })
        self._last_infos = info_list[: len(self._last_labels)]
        html = _build_html(
            self.title_text,
            self._last_points,
            self._last_labels,
            infos=self._last_infos,
            empty=False,
            stage=stage or self.title_text,
        )
        self.view.setHtml(html, QUrl("https://cdn.jsdelivr.net/"))

    def save_figure(self, path):
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            pix = self.view.grab()
            if pix.isNull():
                QTimer.singleShot(0, lambda: None)
                pix = self.grab()
            pix.save(path, "PNG")
            return path
        except Exception:
            try:
                self.grab().save(path, "PNG")
                return path
            except Exception:
                return ""
