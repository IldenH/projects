import init from "./pkg/wasm_hello_world.js";

const runWasm = async () => {
  const helloWorld = await init("./pkg/wasm_hello_world_bg.wasm");
  const addResult = helloWorld.add(24, 24);
  const fibonacciResult = helloWorld.fibonacci(50);
  document.body.textContent = `Hello world! addResult: ${addResult}, fibonacciResult: ${fibonacciResult}`;
};

runWasm();
