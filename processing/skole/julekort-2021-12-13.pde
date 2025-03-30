let ord = ["Snill", "Annerledes", "Rar", "Objektiv", "Adjektiv", "Kul", "Bra", "God", "Myk", "Søt", "Varm", "Åpen", "Human", "Vennlig", "Elskeverdig", "Ikke ond", "Englegod", "Godkynt", "Artig", "Hjetensgod", "Godmodig", "Ufarlig", "Gavmild", "Dumsnill", "Kjærlig", "Velvillig", "Omsorgsfull", "Overbærende", "Høflig", "Jovial", "Ettergivende", "Praktisk Anlagt", "Tolmodig", "Utholdende", "Håvard", "Gul", "Morsom", "Ingenting", "Et til ord på slutten her"]

let notStart = false;

let ordArr = [RandomLol(ord), RandomLol(ord), RandomLol(ord), RandomLol(ord), RandomLol(ord)];


let ordBackup = [ordArr[0], ordArr[1], ordArr[2], ordArr[3], ordArr[4]]

let buttonSize = 600;
let inp;
let navnet = "Uidentifisert_Navn_300xC";

function RandomLol(arr) {
	return arr[Math.floor(Math.random() * (arr.length - 1))];
}

function setup() {
	createCanvas(windowWidth, windowHeight);
	background(200, 0, 0);
	fill(255);
	textSize(30);
	text("Skriv Navnet ditt: ", windowWidth / 2 - 300, 70)

	inp = createInput('');
  inp.position((windowWidth / 2) - buttonSize / 2, ((windowHeight / 2) - buttonSize / 6) - 100);
  inp.size(buttonSize, buttonSize / 3);
	inp.style('font-size', '10vmin');
  inp.input(myInputEvent);

	button = createButton('Submit');
	button.style('font-size', '20vmin');
	button.style('color', 'black');
	button.style('background-color', 'rgb(255)');
  button.position((windowWidth / 2) - buttonSize / 2, ((windowHeight / 2) - buttonSize / 6) + 200);
	button.size(buttonSize, buttonSize / 3)
  button.mousePressed(notStartEqualsTrue);
}

function myInputEvent() {
  navnet = this.value();
}

function notStartEqualsTrue() {
	notStart = true;
}

function draw() {
	if (!notStart) return;
	inp.remove();
	button.remove();

	background(200, 0, 0);
	backgroundDraw();

	if (keyIsDown(32)) {
		for (let i = 0; i < 5; i++) {
			ordArr[i] = "Håvard";
		}
  }
	else {
		for (let i = 0; i < 5; i++) {
			ordArr[i] = ordBackup[i];
		}
	}
	fill(0);
	textSize(60);
	text("God Jul, " + navnet + " Du er:", windowWidth / 2, 150);

	textSize(30);
	textAlign(CENTER);
	text(ordArr[0], windowWidth / 2, 200);
	text(ordArr[1], windowWidth / 2, 250);
	text(ordArr[2], windowWidth / 2, 300);
	text(ordArr[3], windowWidth / 2, 350);
	text(ordArr[4], windowWidth / 2, 400);
}

function backgroundDraw() {
	fill(255)
	rect((windowWidth / 4), 50, windowWidth / 2, 400)

	// SnowMan
	fill(255)
	ellipse(100, windowHeight - 50, 100, 100)
	ellipse(100, windowHeight - 140, 80, 80)
	ellipse(100, windowHeight - 210, 60, 60)
	fill(0)
	rect(50, windowHeight - 250, 100, 25)
	rect(75, windowHeight - 300, 50, 75)
	rect(84, windowHeight - 200, 35, 10)
	ellipse(75, windowHeight - 210, 10, 10)
	ellipse(125, windowHeight - 210, 10, 10)

	// SnowMan 2
	fill(255)
	ellipse(windowWidth - 100, windowHeight - 50, 100, 100)
	ellipse(windowWidth - 100, windowHeight - 140, 80, 80)
	ellipse(windowWidth - 100, windowHeight - 210, 60, 60)
	fill(0)
	rect(windowWidth - 150, windowHeight - 250, 100, 25)
	rect(windowWidth - 125, windowHeight - 300, 50, 75)
	rect(windowWidth - 120, windowHeight - 200, 35, 10)
	ellipse(windowWidth - 75, windowHeight - 210, 10, 10)
	ellipse(windowWidth - 125, windowHeight - 210, 10, 10)
}
