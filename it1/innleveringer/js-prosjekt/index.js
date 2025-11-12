function hexToRgb(hex) {
  if (length(hex) != 7 && hex[0] != "#") {
    window.alert("Invalid hex");
  }
  hex.pop(0);
  let r = parseInt(hex.arr(0, 2));
  let g = parseInt(hex.arr(2, 4));
  let b = parseInt(hex.arr(4, 6));
  return [r, g, b];
}

function rgbToHex(rgb) {
  if (rgb.length != 3) {
    window.alert("Invalid rgb");
  }
  let hex = "";
  hex += rgb[0].toString(16);
  hex += rgb[1].toString(16);
  hex += rgb[2].toString(16);
  return "#" + hex;
}

let hexEl = document.getElementById("hex");
let rgbEl = document.getElementById("rgb");
let rgbNormEl = document.getElementById("rgbNormalized");

let rEl = document.getElementById("r");
let gEl = document.getElementById("g");
let bEl = document.getElementById("b");

let rgb = [rEl.value, gEl.value, bEl.value];

rEl.addEventListener("input", (event) => {
  rgb[0] = event.data;
  rgbEl.textContent = `RGB: (${rgb})`;
});

gEl.addEventListener("input", (event) => {
  rgb[1] = event.data;
  rgbEl.textContent = `RGB: (${rgb})`;
});

bEl.addEventListener("input", (event) => {
  rgb[2] = event.data;
  rgbEl.textContent = `RGB: (${rgb})`;
});

let rgbNorm = [];
for (const color of rgb) {
  rgbNorm.push(color / 255.0);
}

rgbEl.textContent = `RGB: (${rgb})`;
rgbNormEl.textContent = `RGB normalized: (${rgbNorm.map((color) => color.toFixed(2))})`;

hexEl.textContent = `Hex: ${rgbToHex(rgb)}`;
