const fibonacci = (function () {
  const cache = {};

  function fib(n) {
    if (n in cache) return cache[n];
    if (n === 0) return 0;
    if (n === 1) return 1;

    const result = fib(n - 1) + fib(n - 2);
    cache[n] = result;
    return result;
  }

  return fib;
})();

for (let i = 0; i < 1000; i++) {
  let p = document.createElement("p");
  p.textContent = fibonacci(i);
  document.body.appendChild(p);
}
