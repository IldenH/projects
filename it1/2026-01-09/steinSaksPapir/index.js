let moves = {
  Stein: "Saks",
  Saks: "Papir",
  Papir: "Stein",
};

let movesEl = document.getElementById("moves");
for (let move of Object.keys(moves)) {
  let btn = document.createElement("button");
  btn.className = "move";
  btn.textContent = move;
  btn.addEventListener("click", (e) => {
    let userMove = e.target.textContent;
    let computerMove = randMove();
    document.getElementById("computer").textContent = computerMove;
    let winner = chooseWinner(userMove, computerMove);
    document.getElementById("result").textContent = winner;
  });
  movesEl.appendChild(btn);
}

function chooseWinner(user, computer) {
  if (user == computer) return "Uavgjort!";
  else if (moves[user] == computer)
    return user + " slår " + computer + "; Du vant!";
  else if (user == moves[computer])
    return computer + " slår " + user + "; Jeg vant!";
}

function randMove() {
  return Object.keys(moves)[
    Math.floor(Math.random() * Object.keys(moves).length)
  ];
}
