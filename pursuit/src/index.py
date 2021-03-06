from google.appengine.ext import webapp, db
from django.utils import simplejson as json
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from random import random
import JSONError
import model
import logging

def milesToMeters(miles):
    return miles * 609.344

class EmailHandler(webapp.RequestHandler):
    def post(self):
        email = self.request.get("email")
        if not model.Email.getEmail(email):
            model.Email.postEmail(email, self.request)
            self.response.out.write("Thanks, "+email)
        else:
            self.response.out.write("Gotcha. Thanks.")
        
        
class BusinessHandler(webapp.RequestHandler):
    def get(self):
        name = self.request.get("name")
        action = self.request.get("action")
        tv = {}
        if "action" not in self.request.arguments():
            biz = model.Business.getBiz(name=name)
            if biz:
                tv["biz"] = biz
                self.response.out.write(template.render("biz_template.html", tv))
            else:
                self.response.out.write(template.render("biz_intro.html", tv))
        elif action == "getlocs":
            # we want to return entities
            locs, message = model.Business.getBizLocations(name=name)
            logging.log(logging.INFO, message)
            self.response.out.write(json.dumps(locs))
        elif action == "getgames":
            games, message = model.Business.getGames(name=name)
            logging.log(logging.INFO, message)
            self.response.out.write(json.dumps(games))
        elif "name" not in self.request.arguments():
            self.response.out.write(template.render("biz_intro.html", tv))

    def post(self):
        name = self.request.get("name")
        action = self.request.get("action")
        if action == "updateloc":
            lat = self.request.get("lat")
            lon = self.request.get("lon")
            number = self.request.get("number")
            loc, message = model.Business.updateBizLocation(name=name, number=number,lat=lat,lon=lon)
            logging.log(logging.INFO, message)
            self.response.out.write(json.dumps(loc))
        elif action == "setup":
            count = self.request.get("count")
            biz, message = model.Business.create(name=name,count=count)
            logging.log(logging.INFO, message)
            self.redirect("/biz?name=%s"%name)
        elif action == "setuptwitterauth":
            pass
        
class MainHandler(webapp.RequestHandler):
    def get(self):
        c = model.User.all()
        c.order("-time")
        peeps = [i for i in c if not i.isBiz]
        tv = {}
        tv["peeps"] = peeps[:5]
        
        if(self.request.get("see_demo")):
                self.response.out.write(template.render("index.html", tv))
        else:
            self.response.out.write(template.render("tmp_index.html", tv))
        #self.response.out.write("Coming soon.")
        
class ErrorHandler(webapp.RequestHandler):
    def get(self):
        ErrorHandler.error(self)

    @classmethod
    def error(cls, page):
        page.response.out.write("404 Error: Page not found")
        
class RegistrationHandler(webapp.RequestHandler):
    def get(self):
        ErrorHandler.error(self)
        
    def post(self):
        token = self.request.get("access_token")
        logging.info("Saw token of value %s" % token)
        message = RegistrationHandler.registerUser(access_token=token)
        self.response.out.write(message)
    
    @classmethod
    def registerUser(cls, **kwargs):
        message = "Registering user"
        try:
            if "access_token" in kwargs:
                user, message = model.User.create(access_token=kwargs["access_token"])
                user.put()
            elif "name" in kwargs and "id" in kwargs and "friends" in kwargs:
                user = db.GqlQuery("SELECT * FROM User WHERE id=:1",kwargs["id"]).get()
                if not user:
                    user = model.User(name=kwargs["name"], id=kwargs["id"])
                    user.findPlaying(kwargs["friends"])
                    user.put()
                else:
                    message = "User already found in db"
            
            userData = { "id":user.id, "name":user.name }
            logging.info(message)
            return json.dumps({ "message": message, "user": userData })
            
        except Exception, e:
            error = str(e)
            logging.info("Error registering to database: %s" % error)
            return json.dumps({ "message": message, "error": JSONError.GENERIC_ERROR(error) })
            
class UpdateHandler(webapp.RequestHandler):
    def get(self):
        ErrorHandler.error(self)
    
    def post(self):
        id = self.request.get("id")
        lat = self.request.get("lat")
        lon = self.request.get("lon")
        if not (id and lat and lon and TestHandler.isValid(id)):
            self.response.headers["Content-Type"] = "text"
            self.response.out.write("Usage: /get?id=<id>&lon=<lon>&lat=<lat>;")
            return
        message = UpdateHandler.updateUser(id=id, lat=lat, lon=lon)
        self.response.out.write(message)
        
    @classmethod
    def updateUser(cls, **kwargs):
        id = kwargs.pop("id")
        lat = kwargs.pop("lat")
        lon = kwargs.pop("lon")

        message = "Location update"
        # change this to JSON output
        try:
            user = model.UserLocation.update(id=id,lat=lat,lon=lon)
            nearestFriends = model.UserLocation.query(lat=lat,lon=lon,id=id)
            
            logging.info("%s's location updated to (%s,%s)" % (user.name, lat, lon))
            logging.info("Found " if len(nearestFriends) > 0 else "Didn't find " +
                         "friends nearby %s" % "\n".join(["(%s,%s), %s" % (str(i[0]), i[1].user.name, str(i[1].location)) for i in nearestFriends]))
            
            userData = {"id": user.id, "name": user.name, "lon": lon, "lat": lat, "points": user.points}
            friendData = [{"points": i[1].user.points, "id": i[1].user.id, "name": i[1].user.name, "lat": i[1].location.lat, "lon": i[1].location.lon, "distance": milesToMeters(i[0])} for i in nearestFriends]
            toreturn = json.dumps({ "message": message, "user": userData, "friends": friendData })
            return toreturn
        except Exception, e:
            error = str(e)
            toreturn = json.dumps({ "message": message, "error": JSONError.GENERIC_ERROR(error) })
            return toreturn

class PlayHandler(webapp.RequestHandler):
    def get(self):
        ErrorHandler.error(self)

    def post(self):
        p1 = self.request.get("id")
        p2 = self.request.get("p2")
        lat = self.request.get("lat")
        lon = self.request.get("lon")
        action = self.request.get("action")
        message = PlayHandler.makePlay(p1=p1,p2=p2, lat=lat, lon=lon,action=action)
        self.response.out.write(message)        
            
    @classmethod
    def makePlay(cls, **kwargs):
        return model.Game.play(p1=kwargs['p1'], p2=kwargs['p2'], lat=kwargs['lat'], lon=kwargs['lon'], action=kwargs['action'])

class TestHandler(webapp.RequestHandler):
    @classmethod
    def isValid(cls,id):
        try:
            int(id)
        except:
            return False
        return True
    
    def get(self):
        self.names = ["Sam", "Max", "Katie", "Sandra", "Alexander", "John"]
        todo =  self.request.get("todo")
        userId = self.request.get("id")
        if not (todo and userId) or todo == "run":
            self.response.headers["Content-Type"] = "text"
            self.response.out.write("Usage: /test?todo=<get|register>&id=<id> or /test?todo=run")
            return
        
        if todo == "register":
            intId = int(userId)
            name = self.names[intId % len(self.names)]
            message = RegistrationHandler.registerUser(id=userId, name=name, friends=[str(i) for i in range(40)])      
        elif todo == "get":
            lat = self.request.get("lat")
            lon = self.request.get("lon")
            message = UpdateHandler.updateUser(id=userId, lat=lat, lon=lon)
        elif todo == "play":
            p2 = self.request.get("p2")
            lat = self.request.get("lat")
            lon = self.request.get("lon")
            action = self.request.get("action")
            logging.info("Testing out the play mode")
            message = PlayHandler.makePlay(p1=userId, p2=p2, lat=lat, lon=lon, action=action)
        elif todo == "run":
            for i in xrange(20):
                name = self.names[i % len(self.names)]
                message1 = RegistrationHandler.registerUser(id=str(i), name=name, friends=[str(j) for j in xrange(40)])
                message2 = UpdateHandler.updateUser(id=str(i), lat=random(), lon=random())
                self.response.out.write(message1)
                self.response.out.write(message2)
        self.response.out.write(message)        

        
        
application = webapp.WSGIApplication([
    ('/', MainHandler),
    ('/register', RegistrationHandler),
    ('/get', UpdateHandler),
    ('/play', PlayHandler),
    ('/test', TestHandler),
    ('/biz', BusinessHandler),
    ('/addEmail', EmailHandler),
    ('.*', ErrorHandler)
  ])


def main():
    run_wsgi_app(application)


if __name__ == '__main__':
    main()
