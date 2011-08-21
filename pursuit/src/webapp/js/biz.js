function getMap(){
    jQuery.load("/biz?action=getlocs&name="+BIZ_NAME, function(data){
        // we now have the locations.
        locs = $.parseJSON(data);
        setupMap($("#map"), locs);
    });
}

function getTwitter(){
    
}

function getGames(){
    jQuery.load("/biz?action=getgames&name="+BIZ_NAME, function(data){
        games = $.parseJSON(data);
        // games[0] is number of games
        // games[1...n] are locations of other games
        $("#gamecount").html(games[0]);
        setupMap($("#gamelocs"), games[1]);
    });
}


function setupMap(div, locs) {
  var lat = locs[0][0];
  var lon = locs[0][1];
  var myLatlng = new google.maps.LatLng(lat,lon);
  var myOptions = {
    zoom: 4,
    center: myLatlng,
    mapTypeId: google.maps.MapTypeId.ROADMAP
  }
  var map = new google.maps.Map(div, myOptions);
  var markers = [];
  for(var i in locs){
      var marker = new google.maps.Marker({
          position: new google.maps.LatLng(locs[i][0], locs[i][1]);,
          zIndex: i,
          map: map
      });
      markers.push(marker);
  }

  google.maps.event.addListener(div, 'dragend', function(event) {
    for(var i in markers){
        var marker = markers[i];
        if( marker.position == event.latLng ){
            $.post("/biz",
                    {
                     "action": "updateloc",
                     "name": BIZ_NAME,
                     "number": marker.zIndex,
                     "lat": event.latLng.lat(),
                     "lon": event.latLng.lon()
                    },
                    function(data){
                    // should just be confirmation
                        console.log(data);
                    });
        }
    }
  });
}

$(function(){ getMap(); getGames(); });
