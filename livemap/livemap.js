//Factor in game units per pixel
//OFFSET_X = pixelX - gameX / FACTOR_X
//OFFSET_Y = pixelY - gameZ / FACTOR_Y
const FACTOR_X = 3.5131;
const OFFSET_X =  3244 //-172.55;
const FACTOR_Y = -3.512;
const OFFSET_Y = 3061 //12.86;
const IMAGE_SIZE = 6144;

function worldToPixel(gameX, gameZ) {
  const pixelX = gameX / FACTOR_X + OFFSET_X;
  const pixelY = gameZ / FACTOR_Y + OFFSET_Y;
  return { x: pixelX, y: pixelY };
}

function getImageBounds() {
  const mapImage = document.getElementById('map-image');
  const rect = mapImage.getBoundingClientRect();
  const displayedSize = Math.min(rect.width, rect.height);
  const offsetX = rect.left + (rect.width - displayedSize) / 2;
  const offsetY = rect.top + (rect.height - displayedSize) / 2;
  return { offsetX: offsetX, offsetY: offsetY, displayedSize: displayedSize};
}

function moveDot(gameX, gameZ) {
  const pixel = worldToPixel(gameX, gameZ);
  const bounds = getImageBounds();
  // screen size over pixel
  const scale = bounds.displayedSize / IMAGE_SIZE;
  const screenX = bounds.offsetX + pixel.x * scale;
  const screenY = bounds.offsetY + pixel.y * scale;
  const dot = document.getElementById('player-dot');
  dot.style.left = screenX + 'px';
  dot.style.top = screenY + 'px';
}
const socket = new WebSocket('ws://localhost:8765');

socket.onmessage = function(event) {
  const data = JSON.parse(event.data);
  moveDot(data.x, data.z);
  console.log(data.x, data.z);
};
