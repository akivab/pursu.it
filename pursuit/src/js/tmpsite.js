$(function () {
    var img = new Image();
    var ptr = 0;
    var bikes = new Array();
    for(var i = 1; i <= 4; i++)
	var bikes.push(new Image());
    $(img)
	.load(function () {
	    $(this).hide();
   	    $('#bikes').append(this);
	    $(this).fadeIn();
	})
	.attr('src', 'images/logo2.png');
    
    var j = 1;
    for(var i in bikes){
	$(i).load(function(){ $(this).hide(); }).addClass("bike").attr('src', 'images/bike'+j+'.png');
	j++;
    }

    $(bikes)
	.load(function(){
	    $(this).hide();
	    $('#bikes').append(this);
	    $(this).fadeIn();
	})
	.addClass("bike")
	.attr('src', 'images/bike1.png');

    $("#email")
	.addClass("email centered")
	.keyup(function(){
	    setInterval(function(){ $("
	});
		
    
});

