async function fetchChuck() {
  let response = await fetch("https://api.chucknorris.io/jokes/random");
  let data = await response.json();
  console.log(data.value);
}
fetchChuck();
