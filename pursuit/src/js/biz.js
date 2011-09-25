function getMap(){
    $.get("/biz?action=getlocs&name="+BIZ_NAME, function(data){
        // we now have the locations.
        $("#map").html(data);
        locs = $.parseJSON(data);
        setupMap(document.getElementById("map"), locs, {"draggable": false});
    });
}

function getTwitter(){
    
}

function getGames(){
    $.get("/biz?action=getgames&name="+BIZ_NAME, function(data){
        $("gamelocs").html(data);
        games = $.parseJSON(data);
        // games[0] is number of games
        // games[1...n] are locations of players
        $("#gamecount").html(games[0]);
        setupMap(document.getElementById("gamelocs"), games[1], {"draggable": false});
    });
}

function setupMap(div, locs, opts) {

  if(locs.length < 1) return;
  var lat = locs[0]["lat"];
  var lon = locs[0]["lon"];

  var myLatlng = new google.maps.LatLng(lat, lon);
  var myOptions = {
    zoom: 4,
    center: myLatlng,
    mapTypeId: google.maps.MapTypeId.ROADMAP
  }
  var map = new google.maps.Map(div, myOptions);
  var markers = [];
  for(var i in locs){
      var marker = new google.maps.Marker({
          position: new google.maps.LatLng(locs[i]["lat"], locs[i]["lon"]),
          zIndex: parseInt(i),
          draggable: opts["draggable"],
          map: map
      });
      if(opts["draggable"])
       google.maps.event.addListener(marker, 'dragend', function(event) {
        pos = marker.getPosition();
        $.post("/biz",
                {
                 "action": "updateloc",
                 "name": BIZ_NAME,
                 "number": marker.zIndex,
                 "lat": pos.lat(),
                 "lon": pos.lng()
                },
                function(data){
                // should just be confirmation
                    console.log(data);
                });
       });
  }
}

$(function(){ try{ getMap(); } catch(err){ console.log(err); } try{ getGames(); } catch(err){ console.log(err); }  });
