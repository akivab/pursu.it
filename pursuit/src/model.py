#!/usr/bin/env python
#
# Copyright 2008 Brett Slatkin (adapted by Akiva Bamberger)
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Models for Pursuit, adapted from Mutiny game.
"""

__author__ = """
            akiva.bamberger@gmail.com (Akiva Bamberger)
            bslatkin@gmail.com (Brett Slatkin)
            """
            
from google.appengine.api import urlfetch, mail
from django.utils import simplejson as json
from datetime import datetime, timedelta
from google.appengine.ext import db
from random import random
import logging
import math
import time
import JSONError
import geobox


# List of resolutions and slices. Should be in increasing order of size/scope.
GEOBOX_CONFIGS = (
  (4, 5, True),
  (3, 2, True),
  (3, 8, False),
  (3, 16, False),
  (2, 5, False),
)

# Radius of the earth in miles.
RADIUS = 3963.1676

# Time to expire, in seconds
TIME_TO_EXPIRE = 60*15

APP_ID = "186198858096044"
APP_SECRET = "5175bb6a3b05141f0d0ad972acb0cd05"

"""
Helper functions
--------------------
earth_distance: calculates distance between two locations
getUser: returns user for a given id
process: processes a latitude and longitude for use in db
"""

def _earth_distance(lat1, lon1, lat2, lon2):
    lat1, lon1 = math.radians(float(lat1)), math.radians(float(lon1))
    lat2, lon2 = math.radians(float(lat2)), math.radians(float(lon2))
    return RADIUS * math.acos(math.sin(lat1) * math.sin(lat2) +
        math.cos(lat1) * math.cos(lat2) * math.cos(lon2 - lon1))

def getUser(id):
    return db.GqlQuery("SELECT * FROM User WHERE id=:1",id).get()

def process(lat, lon):
    all_boxes = []
    for (resolution, slice, use_set) in GEOBOX_CONFIGS:
            if use_set:
                all_boxes.extend(geobox.compute_set(lat, lon, resolution, slice))
            else:
                all_boxes.append(geobox.compute(lat, lon, resolution, slice))
    return all_boxes, db.GeoPt(lat, lon)

class FBData():
    def __init__(self, **kwargs):
        self.access_token = kwargs["access_token"]
        self.setup()
    
    def setup(self):
        base = "https://graph.facebook.com/me"
        friends = "/friends"
        end = "?access_token=%s" % self.access_token
        logging.info("Trying to setup info with token %s" % self.access_token)
        
        about_me_txt = urlfetch.fetch(base + end).content
        friends_txt = urlfetch.fetch(base + friends + end).content
        logging.info("Data from FB: %s" % about_me_txt)
        self.about_me_json = json.loads(about_me_txt)
        self.friends_json = json.loads(friends_txt)
    
    def getId(self):
        if "id" in self.about_me_json:
            return self.about_me_json["id"]
        raise Exception(self.about_me_json["error"]["message"])
    
    def getName(self):
        if "name" in self.about_me_json:
            return self.about_me_json["name"]
        raise Exception(self.about_me_json["error"]["message"])
    
    def getFriends(self):
        if "data" in self.friends_json:
            return [i["id"] for i in self.friends_json["data"]]
        raise Exception(self.friends_json["error"]["message"])

class Email(db.Model):
    email = db.StringProperty(required=True)
    time = db.DateTimeProperty(auto_now_add=True)
    
    @classmethod
    def getEmail(cls, email):
        return db.GqlQuery("SELECT * FROM Email WHERE email=:1",email).get()
    @classmethod
    def postEmail(cls, email, request):
        Email(email=email).put()
        mail.send_mail(sender="Pursu.it <akiva@wesosmart.com>",
          to="Akiva Bamberger <akiva@pursu.it>",
          subject="%s wants to be kept in the loop" % email,
          body="Email received from %s at time %s and with request %s." % (email, str(datetime.now()), str(request)))
        
class User(db.Model):
    name = db.StringProperty(required=True)
    id = db.StringProperty()
    access_token = db.StringProperty()
    points = db.IntegerProperty(default=0)
    friendsPlaying = db.StringListProperty()
    nowPlaying = db.BooleanProperty(default=False)
    outSince = db.DateTimeProperty(auto_now_add=True)
    isBiz = db.BooleanProperty(default=False)
    time = db.DateTimeProperty(auto_now_add=True)
    
    @classmethod
    def getUser(cls, **kwargs):
        return db.GqlQuery("SELECT * FROM User WHERE id = :1", kwargs.get("id")).get()
        
    def findPlaying(self, friends):
        logging.info("Finding playing friends for player")
        
        for i in xrange(1 + len(friends)/30):
            query = db.GqlQuery("SELECT * FROM User WHERE id in :1", friends[i*30:(i+1)*30])
            results = query.fetch(len(friends))
            
            logging.info("No friends found already" if len(results) is 0 else "Found friends") 
            
            for result in results:
                if self.id is not result.id and result.id not in self.friendsPlaying:
                    logging.info("Found %s and %s playing, adding to db", result.name, self.name)
                    result.friendsPlaying.append(self.id)
                    self.friendsPlaying.append(result.id)
                    result.put()
        
    @classmethod
    def create(cls, **kwargs):
        fb = FBData(**kwargs)
        kwargs["name"] = fb.getName()
        kwargs["id"] = fb.getId()
        newuser = db.GqlQuery("SELECT * FROM User WHERE id=:1",kwargs["id"]).get()
        message = "Found user in db"
        if not newuser: 
            newuser = cls(**kwargs)
            message = "Registering new user"
        friends = fb.getFriends()
        
        newuser.findPlaying(friends)
        
        newuser.put()
        return newuser, message
    
    @classmethod
    def createBiz(cls, **kwargs):
        id = kwargs["id"]
        newuser = db.GqlQuery("SELECT * FROM User WHERE id=:1",kwargs["id"]).get()
        message = "Found user in db"
        if not newuser:
            newuser = cls(**kwargs)
            newuser.isBiz = True
            newuser.put()
            message = "Creating new biz entity"
        return newuser, message

class Business(db.Model):
    name = db.StringProperty()
    entities = db.ListProperty(db.Key)
    twitterauth = db.StringProperty()
    
    @classmethod
    def create(cls, **kwargs):
        numEnt = int(kwargs.pop("count"))
        name = kwargs.pop("name")
        biz = Business.getBiz(name=name)
        message = ""
        if biz:
            message = "Business exists: %s" % str(biz.key)
        if not biz:
            message = "Creating business"
            arr = []
            for i in xrange(numEnt):
                bizId = "%s%d" % (name, i)
                bizUser, msg = User.createBiz(id=bizId, name=name)
                message += msg
                bizUser.put()
                arr.append(bizUser.key())
            biz = Business(name=name, entities=arr)
            biz.put()
        Business.getBizLocations(name=name)
        return biz, message
    
    @classmethod
    def getBiz(cls, **kwargs):
        name = kwargs["name"]
        biz = db.GqlQuery("SELECT * FROM Business WHERE name=:1",name).get()
        return biz
    
    @classmethod
    def getBizLocations(cls, **kwargs):
        biz = Business.getBiz(name=kwargs.get("name"))
        if not biz: return None, "Couldn't get business locations"
        else: message = "Got biz locations"
        ret = []
        for i in User.get(biz.entities):
            loc = UserLocation.getLoc(id=i.id)
            if not loc:
                loc = UserLocation.create(user=i, lat="0", lon="0")
            ret.append({"id": i.id, "lat": loc.location.lat, "lon": loc.location.lon})
        return ret, message
    
    @classmethod
    def getGames(cls, **kwargs):
        biz = Business.getBiz(name=kwargs.get("name"))
        if not biz: return None, "No business found"
        else: message = "Getting games"
        count = 0
        ret = []
        locs = []
        for i in User.get(biz.entities):
            tmp = []
            results = db.GqlQuery("SELECT * FROM Game WHERE p2=:1", i).fetch(500)
            for result in results:
                loc = UserLocation.getLoc(id=result.p2.id)
                tmp.append({"lat": loc.location.lat, "lon": loc.location.lon})
            count += len(tmp)
            locs.extend(tmp)
        ret.append(count)
        ret.append(locs)
        
        return ret, message
        
    @classmethod
    def updateBizLocation(cls, **kwargs):
        biz = Business.getBiz(name=kwargs.get("name"))
        number = int(kwargs.get("number"))
        lat = float(kwargs.get("lat"))
        lon = float(kwargs.get("lon"))
        id =  "%s%d" % (biz.name, number)
        UserLocation.update(id=id,lat=lat, lon=lon, isBiz=True)
        return [id,lat,lon], "Updated location"
      
class UserLocation(db.Model):
    """Represents a single user"s location."""
    user = db.ReferenceProperty(User)
    isBiz = db.BooleanProperty()
    id = db.StringProperty()
    location = db.GeoPtProperty()
    geoboxes = db.StringListProperty()
    time = db.DateTimeProperty(auto_now=True)
    
    @classmethod
    def update(cls, **kwargs):
        lat = kwargs.pop("lat")
        lon = kwargs.pop("lon")
        id = kwargs.pop("id")
        user = getUser(id)
        isBiz = user.isBiz
        
        if not user:
            raise Exception("Did not find user with given id %s" % id)
        else:
            userLocation = db.GqlQuery("SELECT * FROM UserLocation WHERE id=:1",id).get()
            if not userLocation:
                userLocation = UserLocation(user=user, id=user.id, isBiz=isBiz)
            userLocation.geoboxes, userLocation.location = process(lat, lon)
            logging.info("Updating the user location for user %s" % user.name)
            userLocation.put()
            return user
        
    @classmethod
    def getLoc(cls, **kwargs):
        id = kwargs.pop("id")
        result = db.GqlQuery("SELECT * FROM UserLocation WHERE id=:1", id).get()
        return result
        
    
    @classmethod
    def create(cls, **kwargs):
        lat = kwargs.pop("lat")
        lon = kwargs.pop("lon")
        id = kwargs["id"] = kwargs["user"].id
        kwargs["isBiz"] = kwargs["user"].isBiz 
        userLocation = db.GqlQuery("SELECT * FROM UserLocation WHERE id=:1",id).get() 
        if not userLocation:
            kwargs["geoboxes"], kwargs["location"] = process(lat,lon)
            m = cls(**kwargs)
            m.put()
            return m
        else:
            return userLocation
            
    
    @classmethod
    def query(cls, max_results=1, min_params=(0,2), time_limit = TIME_TO_EXPIRE,**kwargs):
        lat = kwargs.pop("lat")
        lon = kwargs.pop("lon")
        id = kwargs.pop("id")
        user = getUser(id)
        if not user:
            raise Exception("User not found in  database")
        
        userLocation = db.GqlQuery("SELECT * FROM UserLocation WHERE id=:1",id).get() 
        if not userLocation:
            logging.info("Querying before updating! A big no-no.")
            return
        logging.info("Looking for friends nearby for %s (has %s as friends)" % (user.name, str(user.friendsPlaying)))            
            
        found_friends = {}
        for params in GEOBOX_CONFIGS[:3]:
            if len(found_friends) >= max_results:
                break
            if params < min_params:
                break
            
            resolution, slice, unused = params
            box = geobox.compute(lat, lon, resolution, slice)
            logging.debug("Searching for box=%s at resolution=%s, slice=%s", 
                          box, resolution, slice)
            
            query = cls.all()
            query.filter("geoboxes =", box)
            query.filter("id in", user.friendsPlaying)
            
            tmp = cls.all()
            tmp.filter("isBiz =", True)
            
            results2 = tmp.fetch(50)
            logging.info("Businesses nearby: %d",  len(results2))

            
            results = query.fetch(50)
            results.extend(results2)
            logging.debug("Found %d results", len(results))
          
            # De-dupe results.
            for result in results:
                if result.id not in found_friends:
                    found_friends[result.id] = result

        # Now compute distances and sort by distance.
        friends_by_distance = []
        for friend in found_friends.itervalues():
            ut = userLocation.time
            ft = friend.time
            date_diff = ut - ft if ut > ft else ft - ut  
            if date_diff.days == 0 and  date_diff.seconds < time_limit:
                distance = _earth_distance(lat, lon, friend.location.lat, friend.location.lon)
                friends_by_distance.append((distance, friend))
            else:
                logging.info("Didn't return result for user %s (time limit: %s)" % (friend.id, str(date_diff)))
        friends_by_distance.sort()
        return friends_by_distance[:max_results]

class Game(db.Model):
    """
    Games class, to handle individual games.
    Games are stored as follows:
    
    When creating a game, we need to do the following:
    1)    Make sure both people can play -- that is, check that either both have
          nowPlaying to false or have optedOut timed out.
    2)    If both can play, set their "play" values to off, and set timestamp to now
    3)    Create a game in which both are playing, waiting for both to OK it
    4a)   When both OK, send back JSON saying "Game on"
    4b)   If one says, "Not OK", set game to OFF,  
    """

    p1 = db.ReferenceProperty(User, collection_name="player1")
    p2 = db.ReferenceProperty(User, collection_name="player2")
    tagger_id = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    p1verified = db.BooleanProperty(default=False)
    p2verified = db.BooleanProperty(default=False)
    gameOn = db.BooleanProperty(default=False)
    
    @classmethod
    def removeStaleGames(cls, **kwargs):
        now = datetime.now()
        since = now - timedelta(seconds=TIME_TO_EXPIRE)
        results = db.GqlQuery("SELECT * FROM Game WHERE created < :1 AND gameOn=:2", since, True).fetch(30)
        count = 0
        for game in results:
            count += 1
            Game.setGameOff(game=game)
        return count > 0
    
    @classmethod
    def setGameOff(cls, **kwargs):
        game = kwargs.pop("game")
        game.gameOn = False
        game.p1.nowPlaying = False
        game.p2.nowPlaying = False
        game.p1.put()
        game.p2.put()
        game.put()
        logging.info("Game set off")
        
    @classmethod
    def setGameOn(cls, **kwargs):
        game = kwargs.pop("game")
        game.gameOn = True
        if not game.p1.isBiz:
            game.p1.nowPlaying = True
        if not game.p2.isBiz:
            game.p2.nowPlaying = True
        game.p1.put()
        game.p2.put()
        game.tagger_id = game.p1.id if game.p2.isBiz or random() < 0.5 else game.p2.id
        logging.info("Game tagger is %s" % game.tagger_id)
        game.put()
        logging.info("Game set on")

    
    @classmethod
    def create(cls, **kwargs):
        p1 = kwargs.pop("p1")
        p2 = kwargs.pop("p2")
        # we assume p1 and p2 are set to nowPlaying if playing.
        # make sure this is set.
        m = {"message": "Can't setup game"}
        
        if not (p1.nowPlaying or (not p2.isBiz and p2.nowPlaying)):
            logging.info("Both players not found playing, going to try to setup a game!")
            newgame = Game(p1=p1,p2=p2)
            Game.setGameOn(game=newgame)

            return Game.getMsg(message="Creating a game", game=newgame, id=p1.id)
        elif (not p2.isBiz and p2.nowPlaying) and not p1.nowPlaying:
            if p2.nowPlaying:
                m['error'] = JSONError.PLAYER_ALREADY_PLAYING(p2)
                return m
        else:
            game = db.GqlQuery("SELECT * FROM Game WHERE p1=:1 AND gameOn=:2", p1, True).get()
            if not game:
                game = db.GqlQuery("SELECT * FROM Game WHERE p2=:1 AND gameOn=:2", p1, True).get()
            if game:
                m = Game.getMsg(message="Creating a game",game=game, id=p1.id)
                return m 
            else:
                logging.info("p1 %s, p2 %s, p2.isBiz %s", p1.id, p2.id, str(p2.isBiz))
                m['error'] = JSONError.CANT_SETUP_GAME()    
                return m
    
    @classmethod
    def getGame(cls, **kwargs):
        p1 = kwargs.pop("p1")
        p2 = kwargs.pop("p2")
        result = db.GqlQuery("SELECT * FROM Game WHERE p1=:1 AND p2=:2 AND gameOn = :3",p1,p2,True).get()
        if not result:
            result = db.GqlQuery("SELECT * FROM Game WHERE p2=:1 AND p1=:2 AND gameOn = :3",p1,p2,True).get()
        return result
    
    @classmethod
    def getMsg(cls, **kwargs):
        """Gets a message for a player"""
        message = kwargs.pop("message")
        game = kwargs.pop("game")
        myId = kwargs.pop("id")
        p = game.p1 if game.p1.id == myId else game.p2
        logging.info("Setting up message for %s and game between %s and %s, tagger is %s", p.name, game.p1.id, game.p2.id, game.tagger_id)
        
        me = UserLocation.getLoc(id = myId)
        you = UserLocation.getLoc(id = game.p1.id if game.p2.id == myId else game.p2.id)
        
        time_left = TIME_TO_EXPIRE - (datetime.now() - game.created).seconds
        
        distance = _earth_distance(you.location.lat, you.location.lon, me.location.lat, me.location.lon)
        gameInfo = { "lat": you.location.lat, "lon": you.location.lon, "id": you.id, 
                    "distance": distance, "time_left": time_left, "points": you.points}
        gameInfo["gameStatus"] = ((game.p1verified or game.p1.isBiz) and (game.p2verified or game.p2.isBiz))
        gameInfo["role"] = 1 if myId == game.tagger_id else 0
        gameInfo["endtime"] = time.mktime((game.created + timedelta(seconds=TIME_TO_EXPIRE)).timetuple())
        return {"message" : message, "game": gameInfo}
    
    @classmethod
    def update(cls, **kwargs):
        """Updates location of a player and returns data about the other player"s location"""
        game = kwargs.pop("game")
        lat = kwargs.pop("lat")
        lon = kwargs.pop("lon")
        id = kwargs.pop("id")
        UserLocation.update(id=id, lat=lat, lon=lon)
        return Game.getMsg(id=id, game=game, message="Updated a user's location in game")
        
    @classmethod
    def verify(cls, **kwargs):
        """Verifies if a user wants to play a game."""
        game = kwargs.pop("game")
        vId = kwargs.pop("id")
        
        if game:
            if vId == game.p1.id and not game.p1verified:
                game.p1verified = True
                game.put()
            elif vId == game.p2.id and not game.p2verified:
                game.p2verified = True
                game.put()
            else:
                return Game.getMsg(message="Didn't need to verify anyone",game=game, id=vId)
            return Game.getMsg(message="Verified player %s" % vId,game=game,id=vId)
        else:
            raise Exception("No game found to verify")
    
    @classmethod
    def play(cls, **kwargs):
        """Plays a game between two people.
        API:
        [+] action=setup:
            sets up a game between two players.
            necessary fields:
                - id : main player
                - p2 : secondary player
        [+] action=verify:
            verifies a game between two players
            necessary fields:
                - id: this player
                - p2: other player
        [+] action=update:
            updates the location of a player in a game
            (similar to get, but with different info)
                - id: this player
                - p2: other player
                - lat: latitude of main player
                - lon: longitude of main player
        [+] action=tag:
            performs a tagging action.
                -id: tagging player
                -p2: tagged player
        """
        p1 = getUser(kwargs.pop("p1"))
        p2 = getUser(kwargs.pop("p2"))
        action = kwargs.pop("action")
        message = {"message": "Trying to play"}
        if not (p1 and p2):
            message['error'] = JSONError.NOT_REGISTERED()
            return json.dumps(message)
        
        logging.debug("Playing between %s and %s with action %s" % (p1.id, p2.id, action))
        
        if Game.removeStaleGames():
                logging.info("Removed stale games.")
        
        if action=="setup":
            logging.info("Trying to setup game for %s" % p1.name)
            message = Game.create(p1=p1, p2=p2)
        elif action=="update":
            logging.info("Trying to update game for %s with lat %s and lon %s" % (p1.name, kwargs["lat"], kwargs["lon"]))
            game = Game.getGame(p1=p1,p2=p2)
            if game:
                message = Game.update(game=game, lat=kwargs["lat"], lon=kwargs["lon"], id=p1.id)
            else:
                message['error'] = JSONError.NO_GAME_TO_UPDATE()
        elif action=="verify":
            logging.info("Trying to verify game for %s" % p1.name)
            game = Game.getGame(p1=p1,p2=p2)
            if game:
                message = Game.verify(id=p1.id, game=game)
            else:
                message['error'] = JSONError.NO_GAME_TO_VERIFY()
        elif action=="decline":
            logging.info("Declining game for %s" % p1.name)
            game = Game.getGame(p1=p1,p2=p2)
            if game:
                Game.setGameOff(game=game)
                message["message"] = "Player successfully declined gameplay"
                message["gameStatus"] = False
            else:
                message['error'] = JSONError.NO_GAME_TO_DECLINE()
        elif action=="tag":
            logging.info("Tagging for %s" % p1.name)
            game = Game.getGame(p1=p1,p2=p2)
            if game:
                if game.p1.id is not game.tagger_id:
                    message['error'] = JSONError.WRONG_TAGGER()
                else:
                    tagger = game.p1
                    other = game.p2
                    l1 = UserLocation.getLoc(id=tagger.id)
                    l2 = UserLocation.getLoc(id=other.id)
                    d = max(1,_earth_distance(l1.location.lat, l1.location.lon, l2.location.lat, l2.location.lon))
                    logging.info("distance: %s", str(d))
                    
                    pChange = int(max(5, 20 / d))
                    tagger.points += pChange
                    tagger.put()
                    
                    if not other.isBiz:
                        other.points -= int(min(pChange, tagger.points/2))
                    
                    Game.setGameOff(game=game)
                    message["message"] = "Player successfully tagged"
                    message["points"] = {p1.id: p1.points, p2.id: p2.points}
                    message["gameStatus"] = False
            else:
                message['error'] = JSONError.NO_GAME_TO_TAG()
        else:
            message["error"] = JSONError.NO_ACTION_TAKEN()

        return json.dumps(message)