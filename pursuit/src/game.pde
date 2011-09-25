// @pjs preload must be used to preload the image
/* @pjs preload="/images/bikeIcon.png"; */
/* @pjs preload="/images/rBikeIcon.png"; */
/* @pjs preload="/images/bBikeIcon.png"; */
/* @pjs preload="/images/horseIcon.png"; */
/* @pjs preload="/images/logo.png"; */
/* @pjs preload="/images/background.png"; */
/* @pjs preload="/images/chatArrow.png"; */
PImage bike;
PImage bBike;
PImage rBike;
PImage horse;
PImage logo;
PImage go;
PImage bar;
PImage bg;
PImage arrow;
float x,y,vx,vy, yt, xt;
float barX, barY;
float logoBarX, logoBarY;
int tmp;
boolean gameStarted;

void setup() {
    size(1,1);
    frameRate(20);
    bike = loadImage("/images/bikeIcon.png");
    rBike = loadImage("/images/rBikeIcon.png");
    bBike = loadImage("/images/bBikeIcon.png");
    tmp = 0;
    bg = loadImage("/images/background.png");
    logo = loadImage("/images/logo_words.png");
    fLogo = loadImage("/images/logo.png");
    go = loadImage("/images/goButton.png");
    bar = loadImage("/images/emailBar.png");
    arrow = loadImage("/images/chatArrow.png");
    strokeWeight(2);
    x = 0;
}

var frame = 0;
var onbar;
var grow;
var impulse;
var bw, bh;
var finalY;
void draw() {

    if(frame < 30)
        $("#game").focus(); 
    if(!grow && frame++ % 2 == 1){
        var w = $(window).width();
        var h = $(window).height() - 1;
        if(w != width || frame==3){
         size(w,h);
         yt = bike.height + 1;
         xt = bike.width;
         y = height - yt;
         vy = 0;
         return;
        }
    }

//    image(bg,0,0,width,height);
    
    if(!grow){
        x += vx;
        y += vy; 
    }
    background(#72afa1)
    image(logo, .5*width-logo.width/2, .5*height-logo.height/2, logo.width, logo.height);


    finalY = logoBarY - logo.height;

    logoBarX = .5*width - logo.width/2;
    logoBarY = .5*height + logo.height*9/60;

    onbar = y < barY && y >= barY - yt && x > barX-bike.width && x < barX + bar.width + go.width/2 && vy >= 0;
    onlogo = y < logoBarY && y >= logoBarY - yt && x > logoBarX-bike.width && x < logoBarX + logo.width && vy >= 0;
    onground = y >= height - yt;
    grow = onlogo && Math.abs(x - (logoBarX + logo.width/2)) < 2*arrow.width;
    if(!grow){
        if(x < 0){ x = 0; vx = 0; }
        if(x > width-xt){ x = width - xt; vx = 0; }
        if(!onlogo && !onbar && !onground) vy += 4;
        else vx *= (Math.abs(vx) > 2 ? (onlogo ? 0.5 : 0.8) : 0);

        if(onlogo || onbar || onground){ 
            y = (onbar ? barY - 15/18*yt : (onlogo ? logoBarY - yt : height-yt)); vy = (Math.abs(vy) < 3 ? 0 : -vy/4); 
        }
    }

    barX = Math.min(width*0.5 + logo.width/2 + 0.5*bar.width, width - bar.width - go.width);    
    if(!grow){
        barY = 2*height/9*Math.sin(frame / 180 * TWO_PI) + 2*height/3;
    }
    else{
        if(Math.abs(finalY - barY) > 5)
            barY = barY + (finalY - barY) * 0.1;
        else if(barY!=finalY){
            barY = finalY;
        }
    }

    $("#email").css("position","fixed").css("top",barY+1).css("left", barX+10).css("zIndex", "99999").css("visibility", "visible").css("width", bar.width-32).css("height", bar.height*2/3);


    image(bar, barX, barY);
    image(go, barX + bar.width, barY);
    if(grow){
        if(bw < bBike.width)
        {
            if(tmp == 0){
                bw = bike.width;
                bh = bike.height;
                tmp++;
//                bike = bBike;
            }
            else{
                bw *= 1.05;
                bh *= 1.05;
            }
            image(bBike, logoBarX + logo.width/2 - bw/2, logoBarY-bh, bw, bh);
            line(logoBarX, logoBarY, logoBarX + logo.width, logoBarY);
        }
        else{
            logo = fLogo;
        }
    }
    else{
        image(arrow, logoBarX + logo.width/2, logoBarY + 3*(5*Math.sin(frame/5) - arrow.height));
        line(logoBarX, logoBarY, logoBarX + logo.width, logoBarY);
        if(impulse < 0)
            image(rBike, x, y);
        else
            image(bike, x, y);
    }
}

void mousePressed(){
    if(Math.pow(mouseX-barX-bar.width, 2)+Math.pow(mouseY-barY,2) < go.width*go.width){
        $.post("/addEmail", {"email": $("#email").attr("value")}, function(data){ $("#email").attr("value", data).attr("disabled", "true"); });
    }
}

void keyPressed(){
    if(!grow && (keyCode == RIGHT || keyCode == LEFT)){ impulse = (keyCode == RIGHT ? 1 : -1);  vx += (vx*impulse >= 0 ? impulse * 5 : -vx /3); }
    else if(!grow && keyCode == UP && (onground || onlogo || onbar)) vy -= 40; 
}
