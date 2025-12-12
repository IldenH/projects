for (let i = 0; i < 500; i++) {
  const flake = document.createElement("div");
  flake.classList.add("snowflake");
  flake.style.left = Math.random() * 100 + "vw";
  flake.style.animationDuration = 5 + Math.random() * 10 + "s";
  flake.style.animationDelay = Math.random() * 5 + "s";
  flake.style.opacity = Math.random();
  flake.style.width = flake.style.height = 2 + Math.random() * 6 + "px";
  document.querySelector(".snow-container").appendChild(flake);
}

for (let i = 0; i < 20; i++) {
  const light = document.createElement("div");
  document.querySelector(".lights").appendChild(light);
}

const date = new Date();
document.getElementById("year").textContent = date.getFullYear();

for (let i = 1; i <= 24; i++) {
  const day = document.createElement("day");
  day.classList.add("day");
  day.textContent = i;
  if (date.getDate() >= i) {
    day.style.backgroundColor = "#fabd2f";
    day.style.color = "#282828";
  } else {
    day.style.backgroundColor = "#282828";
  }
  document.querySelector(".advent").appendChild(day);
}
