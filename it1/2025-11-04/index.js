const shaders = [
  "boxes.frag",
  "gradient.frag",
  "japan.frag",
  "wheel.frag",
  "outline.frag",
  "rainbow.frag",
  "cross.frag",
  "hud.frag",
];

for (const shader of shaders) {
  let canvas = document.createElement("canvas");
  canvas.className = "glslCanvas";
  canvas.setAttribute("data-fragment-url", "shaders/" + shader);
  canvas.width = "500";
  canvas.height = "500";
  document.body.appendChild(canvas);
}
