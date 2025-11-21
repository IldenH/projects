let preview = document.getElementById("preview");

let hexEl = document.getElementById("hex");
let rgbEl = document.getElementById("rgb");
let rgbNormEl = document.getElementById("rgbNorm");

let rgbForm = document.getElementById("rgbForm");
let rgbNormForm = document.getElementById("rgbNormForm");

let forms = [...document.querySelector(".forms").children].filter(
  (el) => el.tagName.toLowerCase() == "form",
);
for (let form of forms) {
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    update(event);
  });
}

let rgb = [0, 0, 0];
let rgbNorm = [0.0, 0.0, 0.0];
let hex = "#000000";

function update(event) {
  if (event) {
    switch (event.target.id) {
      case "hexForm":
        rgb = hexToRgb(event.target["hex"].value);
        break;
      case "rgbForm":
        rgb = ["r", "g", "b"].map((color) =>
          parseInt(event.target[color].value, 10),
        );
        break;
      case "rgbNormForm":
        rgb = ["r", "g", "b"].map((color) =>
          Math.round(parseFloat(event.target[color].value) * 255),
        );
        break;
    }
  }
  hex = rgbToHex(rgb);

  preview.style.backgroundColor = hex;

  rgbEl.textContent = `RGB: (${rgb})`;

  hexEl.value = hex;

  ["r", "g", "b"].map((color, i) => {
    rgbForm[color].value = rgb[i];
  });

  rgbNorm = rgb.map((color) => color / 255.0).map((color) => color.toFixed(2));
  rgbNormEl.textContent = `RGB normalized: (${rgbNorm})`;
  ["r", "g", "b"].map((color, i) => {
    rgbNormForm[color].value = rgbNorm[i];
  });
}

function hexToRgb(hex) {
  if (hex.length != 7 && hex[0] != "#") {
    window.alert("Invalid hex");
  }
  let r = parseInt(hex.slice(1, 3), 16);
  let g = parseInt(hex.slice(3, 5), 16);
  let b = parseInt(hex.slice(5, 7), 16);
  return [r, g, b];
}

function rgbToHex(rgb) {
  if (rgb.length != 3) {
    window.alert("Invalid rgb");
  }
  let hex = "#";
  rgb.map((color) => {
    let part = color.toString(16);
    if (part.length == 1) {
      part = "0" + part;
    }
    hex += part;
  });
  return hex;
}

function copyToClipboard(event) {
  const form = event.target.closest("form").id;
  let text;
  switch (form) {
    case "hexForm":
      text = hex;
      break;
    case "rgbForm":
      text = `(${rgb})`;
      break;
    case "rgbNormForm":
      text = `(${rgbNorm})`;
      break;
  }
  navigator.clipboard.writeText(text);
}

(() => {
  update(null);
})();
