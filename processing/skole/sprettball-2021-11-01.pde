let player;
let score = 0;
let deaths = 0;
let buttonSize = 600;
let notMainMenu = false;
let isChristmas = null;

let boxSpeed = 10;
let playerSpeed = 10;

function random(min, max) {
    return(Math.floor(Math.random(0, max - min))) + min;
}

function setup() {
	createCanvas(windowWidth, windowHeight);
	background(254, 255, 168);

  button = createButton('Start');
	button.style('font-size', '20vmin');
	button.style('color', 'black');
	button.style('background-color', 'rgb(156, 246, 255)');
  button.position((windowWidth / 2) - buttonSize / 2, ((windowHeight / 2) - buttonSize / 6) - 100);
	button.size(buttonSize, buttonSize / 3)
  button.mousePressed(previousSetup);

  buttonChristmas = createButton('Start Christmas Mode');
	buttonChristmas.style('font-size', '10vmin');
	buttonChristmas.style('color', 'black');
	buttonChristmas.style('background-color', 'rgb(0, 220, 0)');
  buttonChristmas.position((windowWidth / 2) - buttonSize / 2, ((windowHeight / 2) - buttonSize / 6) + 200);
	buttonChristmas.size(buttonSize, buttonSize / 3)
  buttonChristmas.mousePressed(previousSetupChristmas);
}

function previousSetup() {
	isChristmas = false;
	button.remove();
	buttonChristmas.remove();
	notMainMenu = true;
  player = new circleClass();
	player.speed = 5;
	makeBoxes();
}

function previousSetupChristmas() {
	isChristmas = true;
	button.remove();
	buttonChristmas.remove();
	notMainMenu = true;
  player = new circleClass();
	player.speed = 5;
	makeBoxes();
}

function makeBoxes() {
	boks = new boxClass();
	boks2 = new boxClass();
	let yakse = random(windowHeight / 2, windowHeight)
	boks.y = yakse
	boks2.y = yakse -= 800
	boxSpeed += 1;
}

function draw() {
	if (notMainMenu) {
		previousDraw();
	}
}

function previousDraw() {
	if (isChristmas) {
		background(0, 220, 0);
	}
	else {
		background(156, 246, 255);
	}
	textSize(windowWidth / 10)
	fill(255)
	text("Score: " + score, 10, 125);
	text("Deaths: " + deaths, 10, 250);

  player.move();
  player.display();

	boks.move();
	boks.display();

	boks2.move();
	boks2.display();

	hit = collidePointRect(player.x, player.y, boks.x, boks.y, boks.sizex, boks.sizey);
	hit2 = collidePointRect(player.x, player.y, boks2.x, boks2.y, boks2.sizex, boks2.sizey);

	if (hit || hit2) {
		boxSpeed = 10;
		makeBoxes();
		score = 0;
		deaths += 1;
	}

	if (boks.x < -100) {
		makeBoxes();
		score += Math.round(random(800, 1000));
	}
}

class boxClass {
	constructor() {
    this.x = windowWidth
    this.y = null;
    this.sizex = 100;
		this.sizey = 600;
		this.speed = boxSpeed;
  }

	move() {
		this.x -= this.speed;
	}
	display() {
		if (isChristmas) {
			fill(219, 53, 53)
		}
		else {
			fill(0, 200, 0)
		}
		noStroke();
		rect(this.x, this.y, this.sizex, this.sizey)
	}
}

class circleClass {
  constructor() {
    this.x = windowWidth / 2
    this.y = windowHeight / 2
    this.diameter = 50;
		this.speed = playerSpeed;
  }

  move() {
		if ((this.x < windowWidth && this.x > 0) && (this.y < windowHeight && this.y > 0)) 
		{
			if (keyIsDown(87) || keyIsDown(38) || keyIsDown(68) || keyIsDown(39)) {
				this.y -= this.speed;
    	}
			else if (keyIsDown(83) || keyIsDown(40) || keyIsDown(65) || keyIsDown(37)) {
				this.y += this.speed;
			}
		}
		else if (this.x > windowWidth) {
			this.x -= this.speed;
		}
		else if (this.x < 0) {
			this.x += this.speed;
		}
		else if (this.y > windowHeight) {
			this.y -= this.speed;
		}
		else if (this.y < 0) {
			this.y += this.speed;
		}
  }

  display() {
		if (isChristmas) {
			fill(123, 3, 252)
		}
		else {
			fill(255, 255, 0)
		}
    ellipse(this.x, this.y, this.diameter, this.diameter);
  }
}
