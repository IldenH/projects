const personer = [
  { navn: "Ola", alder: 25 },
  { navn: "Kari", alder: 30 },
  { navn: "Per", alder: 20 },
  { navn: "Lise", alder: 35 },
  { navn: "Nina", alder: 15 },
  { navn: "Morten", alder: 17 },
];

console.table(personer);

const voksne = personer.filter((p) => p.alder >= 18);
console.table(voksne);

console.log(personer.find((p) => p.alder > 30));

const navns = personer.map((p) => p.navn);
console.log(navns);

const sumAlder = personer.reduce((acc, p) => acc + p.alder, 0);
console.log(sumAlder);

const harVoksen = personer.some((p) => p.alder >= 18);
console.log(harVoksen);

const allVoksen = personer.every((p) => p.alder >= 18);
console.log(allVoksen);

const sortAlder = personer.slice().sort((a, b) => b.alder - a.alder);
console.table(sortAlder);
