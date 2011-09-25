// when the DOM is ready
$(function () {
	var img = new Image();
	
	// wrap our new image in jQuery, then:
	$(img)
	    // once the image has loaded, execute this code
	    .load(function () {
		    $(this).hide();
    		    $('#main').append(this);
		    $(this).fadeIn();
		})
	    
	    .error(function () {
		    // notify the user that the image could not be loaded
		})
	    .addClass("centered")
	    
    
	    // *finally*, set the src attribute of the new image to our image
	    .attr('src', 'images/logo.png');
    });