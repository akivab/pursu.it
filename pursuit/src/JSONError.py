'''
Created on Jul 18, 2011

@author: akiva
'''

def PLAYER_ALREADY_PLAYING(player_id):
    return {'message': "Player %s is already playing" % player_id, "code": 1}

def CANT_SETUP_GAME():
    return {'message': "Can't set up game", "code": 2}

def NOT_REGISTERED():
    return {"message": "Players not yet registered.", "code": 3}
 
def NO_GAME_TO_UPDATE():
    return {"message": "No game found to update", "code": 4}

def NO_GAME_TO_VERIFY():
    return {"message": "No game found to verify", "code": 5}

def NO_ACTION_TAKEN():
    return {"message": "No action taken", "code": 6}

def GENERIC_ERROR(error_string):
    return {"message": error_string, "code": 7}

def NO_GAME_TO_DECLINE():
    return {"message": "No game to decline", "code": 8}
