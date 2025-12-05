let skjema = document.getElementById("skjema");

skjema.addEventListener("submit", (e) => {
  e.preventDefault();

  const formData = new FormData(skjema);
  const data = Object.fromEntries(formData.entries());

  console.log(data);
});
