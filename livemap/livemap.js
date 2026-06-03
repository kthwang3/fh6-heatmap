const FACTOR_X = 3.5131;
const OFFSET_X = 3244;
const FACTOR_Y = -3.512;
const OFFSET_Y = 3061;
const IMAGE_SIZE = 6144;
const BASE_SIZE = 2048;
const MIN_ZOOM = 0.3;
const MAX_ZOOM = 8;

let zoomLevel = 1;
let translateX = (window.innerWidth - BASE_SIZE) / 2;
let translateY = (window.innerHeight - BASE_SIZE) / 2;

const mapInner = document.getElementById('map-inner');
const dot = document.getElementById('player-dot');
const container = document.getElementById('map-container');
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');

function applyTransform() {
  mapInner.style.transform = 'translate(' + translateX + 'px, ' + translateY + 'px) scale(' + zoomLevel + ')';
}

function clamp(value, min, max) {
  if (value < min) return min;
  if (value > max) return max;
  return value;
}

applyTransform();

// ── Zoom to cursor ──
container.addEventListener('wheel', function(event) {
  event.preventDefault();
  let zoomFactor;
  if (event.deltaY < 0) {
    zoomFactor = 1.1;
  } else {
    zoomFactor = 0.9;
  }
  const newZoom = clamp(zoomLevel * zoomFactor, MIN_ZOOM, MAX_ZOOM);
  const cursorX = event.clientX;
  const cursorY = event.clientY;
  translateX = cursorX - (cursorX - translateX) * (newZoom / zoomLevel);
  translateY = cursorY - (cursorY - translateY) * (newZoom / zoomLevel);
  zoomLevel = newZoom;
  applyTransform();
}, { passive: false });

// ── Zoom buttons ──
document.getElementById('zoom-in').addEventListener('click', function() {
  const newZoom = clamp(zoomLevel * 1.3, MIN_ZOOM, MAX_ZOOM);
  const centerX = window.innerWidth / 2;
  const centerY = window.innerHeight / 2;
  translateX = centerX - (centerX - translateX) * (newZoom / zoomLevel);
  translateY = centerY - (centerY - translateY) * (newZoom / zoomLevel);
  zoomLevel = newZoom;
  applyTransform();
});

document.getElementById('zoom-out').addEventListener('click', function() {
  const newZoom = clamp(zoomLevel * 0.77, MIN_ZOOM, MAX_ZOOM);
  const centerX = window.innerWidth / 2;
  const centerY = window.innerHeight / 2;
  translateX = centerX - (centerX - translateX) * (newZoom / zoomLevel);
  translateY = centerY - (centerY - translateY) * (newZoom / zoomLevel);
  zoomLevel = newZoom;
  applyTransform();
});

// ── Drag to pan ──
let isDragging = false;
let dragStartX = 0;
let dragStartY = 0;
let dragStartTranslateX = 0;
let dragStartTranslateY = 0;

container.addEventListener('mousedown', function(event) {
  event.preventDefault();
  isDragging = true;
  dragStartX = event.clientX;
  dragStartY = event.clientY;
  dragStartTranslateX = translateX;
  dragStartTranslateY = translateY;
  container.style.cursor = 'grabbing';
});

document.addEventListener('mousemove', function(event) {
  if (!isDragging) return;
  translateX = dragStartTranslateX + (event.clientX - dragStartX);
  translateY = dragStartTranslateY + (event.clientY - dragStartY);
  applyTransform();
});

document.addEventListener('mouseup', function() {
  isDragging = false;
  container.style.cursor = 'grab';
});

// ── Touch pan + pinch zoom ──
let lastTouchX = 0;
let lastTouchY = 0;
let lastPinchDist = 0;

container.addEventListener('touchstart', function(event) {
  event.preventDefault();
  if (event.touches.length === 1) {
    lastTouchX = event.touches[0].clientX;
    lastTouchY = event.touches[0].clientY;
  } else if (event.touches.length === 2) {
    const dx = event.touches[0].clientX - event.touches[1].clientX;
    const dy = event.touches[0].clientY - event.touches[1].clientY;
    lastPinchDist = Math.sqrt(dx * dx + dy * dy);
  }
}, { passive: false });

container.addEventListener('touchmove', function(event) {
  event.preventDefault();
  if (event.touches.length === 1) {
    const dx = event.touches[0].clientX - lastTouchX;
    const dy = event.touches[0].clientY - lastTouchY;
    translateX = translateX + dx;
    translateY = translateY + dy;
    lastTouchX = event.touches[0].clientX;
    lastTouchY = event.touches[0].clientY;
    applyTransform();
  } else if (event.touches.length === 2) {
    const dx = event.touches[0].clientX - event.touches[1].clientX;
    const dy = event.touches[0].clientY - event.touches[1].clientY;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const newZoom = clamp(zoomLevel * (dist / lastPinchDist), MIN_ZOOM, MAX_ZOOM);
    const centerX = (event.touches[0].clientX + event.touches[1].clientX) / 2;
    const centerY = (event.touches[0].clientY + event.touches[1].clientY) / 2;
    translateX = centerX - (centerX - translateX) * (newZoom / zoomLevel);
    translateY = centerY - (centerY - translateY) * (newZoom / zoomLevel);
    zoomLevel = newZoom;
    lastPinchDist = dist;
    applyTransform();
  }
}, { passive: false });

// ── Position ──
function worldToPixel(gameX, gameZ) {
  const pixelX = gameX / FACTOR_X + OFFSET_X;
  const pixelY = gameZ / FACTOR_Y + OFFSET_Y;
  return { x: pixelX, y: pixelY };
}

function moveDot(gameX, gameZ) {
  const pixel = worldToPixel(gameX, gameZ);
  const scale = BASE_SIZE / IMAGE_SIZE;
  dot.style.left = (pixel.x * scale) + 'px';
  dot.style.top = (pixel.y * scale) + 'px';
  dot.style.display = 'block';
}

// ── WebSocket ──
function connect() {
  const socket = new WebSocket('ws://' + window.location.hostname + ':8765');

  socket.onopen = function() {
    statusDot.className = 'connected';
    statusText.textContent = 'Connected';
  };

  socket.onclose = function() {
    statusDot.className = 'error';
    statusText.textContent = 'Disconnected';
    setTimeout(connect, 2000);
  };

  socket.onerror = function() {
    statusDot.className = 'error';
    statusText.textContent = 'Error';
  };

  socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    moveDot(data.x, data.z);
  };
}

connect();
