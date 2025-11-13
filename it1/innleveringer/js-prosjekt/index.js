let hexEl = document.getElementById("hex");
let rgbEl = document.getElementById("rgb");
let rgbNormEl = document.getElementById("rgbNorm");
let rgbNormForm = document.getElementById("rgbNormForm");

let rgbForm = document.getElementById("rgbForm");
rgbForm.addEventListener("submit", (event) => {
  event.preventDefault();
  update();
});

function update() {
  let rgb = ["r", "g", "b"].map((color) => parseInt(rgbForm[color].value, 10));
  let rgbNorm = rgb.map((color) => color / 255.0);

  rgbEl.textContent = `RGB: (${rgb})`;
  rgbNormEl.textContent = `RGB normalized: (${rgbNorm.map((color) => color.toFixed(2))})`;
  hexEl.value = `${rgbToHex(rgb)}`;
}

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

(() => {
  update();
})();
