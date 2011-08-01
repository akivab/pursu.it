// @pjs preload must be used to preload the image
/* @pjs preload="images/bikeIcon.png"; */
/* @pjs preload="images/horseIcon.png"; */
/* @pjs preload="images/logo.png"; */
PImage bike;
PImage horse;
PImage logo;
PImage go;
float x,y,vx,vy;
boolean gameStarted;

void setup() {
    size(800,500);
    frameRate(20);
    bike = loadImage("images/bikeIcon.png");
    horse = loadImage("images/horseIcon.png");
    logo = loadImage("images/logo.png");
    go = loadImage("images/goButton.png");
    strokeWeight(2);
    buttonX = width-100;
    buttonY = 0;
    x = 0;
    y = 400;
    vy = 2;
}

void draw() {
  background(#72afa1);
  image(logo, 300, 180);
  if(gameStarted)
      image(horse, x, y);
  else
      image(go, buttonX, buttonY);
  y = max(min(height-bike.height, y+vy), 0);
  vy += 2;
  x = max(min(width-bike.width, x+vx), -1);
  //  ellipse(mouseX,mouseY,10,10);
}

void keyPressed() {
    if (key == CODED) {
	if (keyCode == UP) {
	    vy = -20;
	} else if (keyCode == DOWN) {
	    y += 5;
	} else if (keyCode == LEFT) {
	    if(vx > 0) vx = 0;
	    else if (vx <= -4) vx = -4;
	    else vx -= 1;	
	} else if (keyCode == RIGHT) {
	    if(vx < 0) vx = 0;
	    else if (vx >= 4) vx = 4;
	    else vx += 1;
	}
    }
}

void mousePressed(){
    if(mouseX > buttonX && mouseX < buttonX + go.width && mouseY > buttonY && mouseY < buttonY + go.height){
	gameStarted = true;
    }
}