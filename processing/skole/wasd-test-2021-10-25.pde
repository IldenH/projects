function setup() {
	createCanvas(windowWidth, windowHeight);
	background(100);

	CubeX = 20
	CubeY = 20
	CubeSizeX = 20
	CubeSizeY = 20
}

function draw() {
  if (isKeyPressed) {
    if (key == 'w' || key == 'W') {
      fill(255, 0, 0);
			CubeY -= 10
    }
		else if (key == 'a' || key == 'A') {
			fill(0, 255, 0);
			CubeX -= 10
		}
		else if (key == 's' || key == 'S') {
      fill(0, 0, 255);
			CubeY += 10
    }
		else if (key == 'd' || key == 'D') {
			fill(255, 255, 0);
			CubeX += 10
		}
		else {
			fill(255);
		}
	}
  rect(CubeX, CubeY, CubeSizeX, CubeSizeY);
}
