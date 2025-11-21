let preview = document.getElementById("preview");

let hexEl = document.getElementById("hex");
let rgbEl = document.getElementById("rgb");
let rgbNormEl = document.getElementById("rgbNorm");

let rgbForm = document.getElementById("rgbForm");
let rgbNormForm = document.getElementById("rgbNormForm");

let hslForm = document.getElementById("hslForm");
let saturationSlider = hslForm.querySelector(".saturation");
let lightSlider = hslForm.querySelector(".light");

let forms = [...document.querySelector(".forms").children].filter(
  (el) => el.tagName.toLowerCase() == "form",
);
for (let form of forms) {
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    update(event.target);
  });
}

hslForm
  .querySelectorAll('input[type="range"], input[type="number"]')
  .forEach((el) => {
    el.addEventListener("input", () => {
      const pairName = el.name.replace(/(Num|Range)$/, "");
      const otherType = el.name.endsWith("Num") ? "Range" : "Num";
      const other = document.querySelector(`[name="${pairName}${otherType}"]`);
      if (other) other.value = el.value;
    });
    el.addEventListener("change", () => update(hslForm));
  });

let rgb = [0, 0, 0];
let rgbNorm = [0.0, 0.0, 0.0];
let hex = "#000000";
let hsl = [0, 0, 0];

function update(form) {
  if (form) {
    switch (form.id) {
      case "hexForm":
        rgb = hexToRgb(form["hex"].value);
        break;
      case "rgbForm":
        rgb = ["r", "g", "b"].map((color) => parseInt(form[color].value, 10));
        break;
      case "rgbNormForm":
        rgb = ["r", "g", "b"].map((color) =>
          Math.round(parseFloat(form[color].value) * 255),
        );
        break;
      case "hslForm":
        let _hsl = ["hue", "saturation", "light"].map((channel, _) =>
          parseInt(form[channel + "Num"].value, 10),
        );
        rgb = hslToRgb(_hsl);
        break;
    }
  }
  hex = rgbToHex(rgb);
  hsl = rgbToHsl(rgb);

  saturationSlider.style.background = `linear-gradient(to right,
  hsl(${hsl[0]}, 0%, ${hsl[2]}%),
  hsl(${hsl[0]}, 100%, ${hsl[2]}%)
)`;
  lightSlider.style.background = `linear-gradient(to right,
  hsl(${hsl[0]}, ${hsl[1]}%, 0%),
  hsl(${hsl[0]}, ${hsl[1]}%, 50%),
  hsl(${hsl[0]}, ${hsl[1]}%, 100%)
)`;

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

  ["hue", "saturation", "light"].map((channel, i) => {
    hslForm[channel + "Num"].value = hsl[i];
    hslForm[channel + "Range"].value = hsl[i];
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

// https://stackoverflow.com/questions/2353211/hsl-to-rgb-color-conversion
function hueToRgb(p, q, t) {
  if (t < 0) t += 1;
  if (t > 1) t -= 1;
  if (t < 1 / 6) return p + (q - p) * 6 * t;
  if (t < 1 / 2) return q;
  if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
  return p;
}

// https://stackoverflow.com/questions/2353211/hsl-to-rgb-color-conversion
function hslToRgb(hsl) {
  if (hsl.length != 3) {
    window.alert("Invalid hsl");
  }
  let h = hsl[0] / 360.0;
  let s = hsl[1] / 100.0;
  let l = hsl[2] / 100.0;

  let r, g, b;

  if (s === 0) {
    r = g = b = l; // achromatic
  } else {
    const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p = 2 * l - q;
    r = hueToRgb(p, q, h + 1 / 3);
    g = hueToRgb(p, q, h);
    b = hueToRgb(p, q, h - 1 / 3);
  }

  return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
}

// https://stackoverflow.com/questions/2353211/hsl-to-rgb-color-conversion
function rgbToHsl(rgb) {
  if (rgb.length != 3) {
    window.alert("Invalid rgb");
  }
  let r = rgb[0] / 255.0;
  let g = rgb[1] / 255.0;
  let b = rgb[2] / 255.0;

  const vmax = Math.max(r, g, b),
    vmin = Math.min(r, g, b);
  let h,
    s,
    l = (vmax + vmin) / 2;

  if (vmax === vmin) {
    return [0, 0, Math.round(l * 100)]; // achromatic
  }

  const d = vmax - vmin;
  s = l > 0.5 ? d / (2 - vmax - vmin) : d / (vmax + vmin);
  if (vmax === r) h = (g - b) / d + (g < b ? 6 : 0);
  if (vmax === g) h = (b - r) / d + 2;
  if (vmax === b) h = (r - g) / d + 4;
  h /= 6;

  return [Math.round(h * 360), Math.round(s * 100), Math.round(l * 100)];
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
    case "hslForm":
      text = `(${hsl[0]}, ${hsl[1]}%, ${hsl[2]}%)`;
      break;
  }
  navigator.clipboard.writeText(text);
}

(() => {
  update(null);
})();
