class Fruit {
  constructor(name, src, desc, liked) {
    this.name = name;
    this.src = src;
    this.desc = desc;
    this.liked = liked;
  }
}

let fruits = [
  new Fruit("Apple", "assets/apple.jpg", "Apples are red", false),
  new Fruit("Banana", "assets/apple.jpg", "Bananas are yellow", false),
];

let imgEl = document.getElementById("img");
let nameEl = document.getElementById("name");
let descEl = document.getElementById("desc");
let heartEl = document.getElementById("heart");
let dislikeEl = document.getElementById("dislike");

let currentFruit = 0;

function changeFruit(liked) {
  let fruit = fruits[currentFruit];
  fruit.liked = liked;
  console.log(fruit);

  imgEl.src = fruit.src;
  imgEl.alt = fruit.name;
  nameEl.textContent = fruit.liked ? fruit.name + " :)" : fruit.name;
  descEl.textContent = fruit.desc;

  if (currentFruit >= fruits.length - 1) {
    analysisScreen();
  } else {
    currentFruit += 1;
  }
}

heartEl.addEventListener("click", () => {
  changeFruit(true);
});

dislikeEl.addEventListener("click", () => {
  changeFruit(false);
});

function analysisScreen() {
  let main = document.querySelector("main");
  main.style = "display: none";
  for (fruit of fruits) {
    let fruitDiv = document.createElement("div");
    let imgEl = document.createElement("img");
    imgEl.id = "img";
    imgEl.src = fruit.src;
    let nameEl = document.createElement("h3");
    nameEl.id = "name";
    nameEl.textContent = fruit.liked ? fruit.name + " :)" : fruit.name;
    let descEl = document.createElement("p");
    descEl.id = "desc";
    descEl.textContent = fruit.desc;
    fruitDiv.appendChild(imgEl);
    fruitDiv.appendChild(nameEl);
    fruitDiv.appendChild(descEl);
    document.body.appendChild(fruitDiv);
  }
}
