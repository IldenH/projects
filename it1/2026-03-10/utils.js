export async function getData(endpoint) {
  const response = await fetch(`http://127.0.0.1:3000/api/${endpoint}`);
  const data = response.json();
  return data;
}
