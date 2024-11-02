/*
  Johan Karlsson, 2020
  https://twitter.com/DonKarlssonSan
  MIT License, see Details View
*/
let canvas;
let ctx;
let w, h;
let config = {
  squareSize: 60,
  space: 4,
  lineWidth: 2,
};

function setup() {
  canvas = document.querySelector("#canvas");
  ctx = canvas.getContext("2d");
  reset();
  window.addEventListener("resize", () => {
    reset();
    draw();
  });  
}

function reset() {
  w = canvas.width = window.innerWidth;
  h = canvas.height = window.innerHeight; 
}

function draw() {
  ctx.fillStyle = "white";
  ctx.fillRect(0, 0, w, h);
  let size = config.squareSize;
  let dist = Math.sqrt(2 * size * size);
  for(let x = -dist; x < w + dist; x += dist) {
    for(let y = -1; y < h / dist * 2 + 1; y += 1) {
      let xOffset = 0;
      if(Math.abs(y) % 2 === 1) {
        xOffset = dist / 2;
      }
      drawLines(x + xOffset, y * dist / 2, size);
    }
  }
}

function setRandomRotationOnContext() {
  let sign = Math.random() > 0.5 ? -1 : 1;
  let angle = sign * Math.PI / 4;
  ctx.rotate(angle);
}

function getSaturationOffset(x0, y0) {
  let xDist = w / 2 - x0;
  let yDist = h / 2 - y0;
  let satOffset = 75 - Math.sqrt(xDist * xDist + yDist * yDist) / w * 60;
  return satOffset;
}


function drawLines(x0, y0, length) {
  ctx.save();
  let cx = x0 + length / 2;
  let cy = y0 + length / 2;
  ctx.translate(cx, cy);
  setRandomRotationOnContext();
  let lineWidth = config.lineWidth;
  ctx.lineWidth = lineWidth;
  let hl = lineWidth / 2;
  let xDist = w / 2 - x0;
  let yDist = h / 2 - y0;
  let hue = Math.random() * 10 + 30;
  let satOffset = getSaturationOffset(x0, y0);
  for(let i = -hl; i < length + hl; i += lineWidth) {
    ctx.beginPath();
    let saturation = Math.round(Math.random() * 25) + satOffset;
    let color = `hsl(${hue}, ${saturation}%, 50%)`;
    ctx.strokeStyle = color;
    ctx.moveTo(-length / 2 - hl, i - length / 2);
    ctx.lineTo(length / 2 + hl, i - length / 2);
    ctx.stroke();
  }
  ctx.strokeStyle = "gray";
  ctx.lineWidth = config.space;
  ctx.strokeRect(-length / 2, -length / 2, length, length);
  ctx.restore();
}

setup();
draw();