import StringIO
import json
import logging
import random
import urllib
import urllib2
import random
import copy

# for sending images
from PIL import Image
import multipart

# standard app engine imports
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2

TOKEN = '223076889:AAGAB7wQ_7xTokH7E6SJOSSvm9Uqa0NdZSA'

BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'

# ================================

class EnableStatus(ndb.Model):
    # key name: str(chat_id)
    enabled = ndb.BooleanProperty(indexed=False, default=False)


# ================================

def setEnabled(chat_id, yes):
    es = EnableStatus.get_or_insert(str(chat_id))
    es.enabled = yes
    es.put()

def getEnabled(chat_id):
    es = EnableStatus.get_by_id(str(chat_id))
    if es:
        return es.enabled
    return False

# ================================


class Player():
    def __init__(self, num, name):
        self.id = num
        self.name = str(name)


class Vote():
    def __init__(self, num):
        if num == 0:
            self.vote = False
        else:
            self.vote = True

class Game():
    def __init__(self):
        #general game rule data
        self.identityDictRS = {5:(3,2), 6:(4,2), 7:(4,3), 8:(5,3), 9:(6,3), 10:(6,4)}
        self.missionDict = {5:(0,2,3,2,3,3), 6:(0,2,3,3,3,4), 7:(0,2,3,3,4,4), 8:(0,3,4,4,5,5), 9:(0,3,4,4,5,5), 10:(0,3,3,4,4,5)}  #first left as blank, if 7 players and above need 2 fails to fail mission 4

        #general game attributes
        self.playerIDList = []
        self.missionNum = 1
        self.roundNum = 1
        self.resistance = []
        self.spies = []
        self.missionProgress = []
        self.numPlayers = 0
        self.numSuccesses = []
        self.numFails = []
        self.gameOver = False
        self.numSpies = 0
        self.numResistance = 0
        self.printer = "Welcome to The Resistance!"

        #selection phase attributes
        self.goingOnMission = []
        self.currLeader = 0

        #voting phase attributes
        self.yesCount = 0
        self.noCount = 0

        #mission phase attributes
        self.successCount = 0
        self.failCount = 0

        #Phase attributes
        self.playerAdditionPhase = True
        self.selectionPhase = False
        self.votingPhase = False
        self.missionPhase = False
        #print ("Welcome to The Resistance!")
		
    def __str__(self):
	    return self.printer
		
    def whatstate(self):
        if self.playerAdditionPhase == True:
            return "Player Addition Phase"
        elif self.selectionPhase == True:
            return "Selection Phase"
        elif self.votingPhase == True:
            return "Voting Phase"
        elif self.missionPhase == True:
            return "Mission Phase"
        else:
            return "all false"		
	
    def sortplayers(self):
        if len(self.playerIDList) > 4 :
            self.playerAdditionPhase = False
            self.selectionPhase = True
            self.numPlayers = len(self.playerIDList)
            self.numSpies = self.identityDictRS[self.numPlayers][1]
            self.numResistance = self.identityDictRS[self.numPlayers][0]
            playercopy = copy.deepcopy(self.playerIDList)
            for i in range(0, self.numSpies):
                self.spies.append(playercopy.pop(random.randint(0,self.numPlayers-i-1)))
            self.resistance = copy.deepcopy(playercopy)                    
            #assign players to teams, send out private messages to players
            self.printer = ("The game has begun! Let us proceed to the first round of voting! ") + (self.playerIDList[self.currLeader].name + " will choose who he/she wants to go on the first mission")
            #print ("The game has begun! Let us proceed to the first round of voting!")
            #print (self.playerIDList[self.currLeader].name + " will choose who he/she wants to go on the first mission")
        else:
            self.printer = "Not enough users to play"
            #print ("Not enough users to play")
                    	
    def give(self, arg):

        if isinstance(arg, str):
            if arg == "reset":
                self.playerIDList = []
                self.missionNum = 1
                self.roundNum = 1
                self.resistance = []
                self.spies = []
                self.missionProgress = []
                self.numPlayers = 0
                self.numSuccesses = []
                self.numFails = []
                self.gameOver = False
                self.numSpies = 0
                self.numResistance = 0
                self.printer = "Game has been restarted, Welcome to The Resistance!"

                #selection phase attributes
                self.goingOnMission = []
                self.currLeader = 0

                #voting phase attributes
                self.yesCount = 0
                self.noCount = 0

                #mission phase attributes
                self.successCount = 0
                self.failCount = 0

                #Phase attributes
                self.playerAdditionPhase = True
                self.selectionPhase = False
                self.votingPhase = False
                self.missionPhase = False
                #print ("Game has been restarted, Welcome to The Resistance!")


        if (self.gameOver == True):
            self.printer = "Game is over, Thanks for playing!"
            #print ("Game is over, Thanks for playing!")

        #Addition phase, adding of players to the game instance
        elif self.playerAdditionPhase == True:
            if isinstance(arg, Player):
                self.playerIDList += [arg]
                self.printer = (str(arg.name) + " has joined the game!")
                #print (str(arg.name) + " has joined the game!")
            if len(self.playerIDList) == 10:
				self.sortplayers()
            if isinstance(arg, str):
                if arg == "start":
                    self.sortplayers()
        #Selection phase, curr Leader gets to choose who he wants to go for the mission
        elif self.selectionPhase == True:
            if isinstance(arg, Player):
                if arg not in self.goingOnMission:
                    self.goingOnMission += [arg]
                    self.printer =(arg.name + " has been chosen to go for the mission")
                    #print (arg.name + " has been chosen to go for the mission")
                else:
                    self.printer = ("Please choose someone else who is not going on the mission already")
                    #print ("Please choose someone else who is not going on the mission already") #should be private chatted

            if len(self.goingOnMission) == self.missionDict[self.numPlayers][self.missionNum]:
                line = ""
                for ele in self.goingOnMission:
                    line += str(ele.name) + ", "
                line += "are going on a mission! Vote to decide if you want these guys on the mission"
                self.printer = line
                #print (line)
                self.selectionPhase = False
                self.votingPhase = True
            
            #print ("WRONG INPUT1") #it's okay cause nothing happens if trash is sent here


        elif self.votingPhase == True:
            if isinstance(arg, Vote):
                if arg.vote == True:
                    self.yesCount += 1
                elif arg.vote == False:
                    self.noCount += 1
                if self.yesCount + self.noCount == self.numPlayers:
                    if (self.yesCount > self.noCount):
                        self.votingPhase = False
                        self.missionPhase = True
                        line = ""
                        for ele in self.goingOnMission:
                            line += str(ele.name) + ", "
                        line += "are going on a mission! Reply to determine if the mission will Succeed or Fail!" #need to send our private messages
                        self.printer = line
                        #print (line)
                        self.roundNum = 1
                        self.yesCount = 0
                        self.noCount = 0
                    else:
                        self.yesCount = 0
                        self.noCount = 0
                        self.votingPhase = False
                        self.selectionPhase = True
                        self.roundNum += 1
                        self.currLeader = (self.currLeader + 1)%self.numPlayers
                        if self.roundNum < 5:
                            self.printer = ("Insufficient Yes votes to proceed, " + str(self.playerIDList[self.currLeader].name) +
                                   " will now choose his/her merry men to go on the mission!")
                            #print ("Insufficient Yes votes to proceed, " + str(self.playerIDList[self.currLeader].name) +
                                   #" will now choose his/her merry men to go on the mission!")
                        self.goingOnMission = []
                        if self.roundNum == 6:
                            self.printer = ("Insufficient Yes votes to proceed, the spies have cause sufficient chaos to confuse the resistance")
                            #print ("Insufficient Yes votes to proceed, the spies have cause sufficient chaos to confuse the resistance")
                            self.spiesWin()
            else:
                self.printer = ("WRONG INPUT2")
                #print ("WRONG INPUT2")

        elif self.missionPhase == True:
            if isinstance(arg, Vote):
                if arg.vote == True:
                    self.successCount += 1
                else:
                    self.failCount += 1
                if self.successCount + self.failCount == len(self.goingOnMission):
                    if (self.failCount == 0) or (self.numPlayers >= 7 and self.failCount <= 1 and self.missionNum == 4): #due to technicality that requires 2 fails on mission 4 for 7 and more players for a mission to fail
                        self.numSuccesses += [self.missionNum]
                        self.printer = ("Mission " + str(self.missionNum) + " has been successful!")
                        #print ("Mission " + str(self.missionNum) + " has been successful!")
                        #print
                        self.currLeader = (self.currLeader + 1)%self.numPlayers
                        #mission success
                    else:
                        self.numFails += [self.missionNum]
                        self.printer = ("Mission " + str(self.missionNum) + " has ended in failure!")
                        #print ("Mission " + str(self.missionNum) + " has ended in failure!")
                        #print
                        self.currLeader = (self.currLeader + 1)%self.numPlayers
                        #mission fail

                    if (len(self.numSuccesses) == 3):
                        self.resistanceWin()

                    if (len(self.numFails) == 3):
                        self.spiesWin()

                    if self.gameOver == False:
                        self.printer += (str(self.playerIDList[self.currLeader].name) + " will now choose who will go for the next mission")
                        #print (str(self.playerIDList[self.currLeader].name) + " will now choose who will go for the next mission")
                        self.goingOnMission = []
                        self.missionNum += 1
                        self.selectionPhase = True
                        self.missionPhase = False
                        self.successCount= 0
                        self.failCount = 0
            else:
                self.printer = ("WRONG INPUT3")
                #print ("WRONG INPUT3")


                        
    def spiesWin(self):
        self.gameOver = True
        self.missionPhase = False
        self.printer = ("Congratulations, the Spies have Won!")
        #print ("Congratulations, the Spies have Won!")

    def resistanceWin(self):
        self.gameOver = True
        self.missionPhase = False
        self.printer = ("Congratulations, the Resistance has reigned supreme!")
        #print ("Congratulations, the Resistance has reigned supreme!")

	
	
# ================================
gamestate = Game()

# ================================

class MeHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getMe'))))


class GetUpdatesHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getUpdates'))))


class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        url = self.request.get('url')
        if url:
            self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'setWebhook', urllib.urlencode({'url': url})))))


class WebhookHandler(webapp2.RequestHandler):
    def post(self):
        urlfetch.set_default_fetch_deadline(60)
        body = json.loads(self.request.body)
        logging.info('request body:')
        logging.info(body)
        self.response.write(json.dumps(body))

        update_id = body['update_id']
        message = body['message']
        message_id = message.get('message_id')
        date = message.get('date')
        text = message.get('text')
        fr = message.get('from')
        chat = message['chat']
        chat_id = chat['id']

        if not text:
            logging.info('no text')
            return

        def reply(msg=None, img=None):
            if msg:
                resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
                    'chat_id': str(chat_id),
                    'text': msg.encode('utf-8'),
                    'disable_web_page_preview': 'true',
                    #'reply_to_message_id': str(message_id),
                })).read()
            elif img:
                resp = multipart.post_multipart(BASE_URL + 'sendPhoto', [
                    ('chat_id', str(chat_id)),
                    ('reply_to_message_id', str(message_id)),
                ], [
                    ('photo', 'image.jpg', img),
                ])
            else:
                logging.error('no msg or img specified')
                resp = None

            logging.info('send response:')
            logging.info(resp)

        if text.startswith('/'):
            if text == '/start': 
                reply('Bot enabled')
                setEnabled(chat_id, True)
            elif text == '/stop':
                reply('Bot disabled')
                setEnabled(chat_id, False)
            elif text == '/image':
                img = Image.new('RGB', (512, 512))
                base = random.randint(0, 16777216)
                pixels = [base+i*j for i in range(512) for j in range(512)]  # generate sample image
                img.putdata(pixels)
                output = StringIO.StringIO()
                img.save(output, 'JPEG')
                reply(img=output.getvalue())
            elif text == '/reset':
                gamestate.give("reset")
                reply(str(gamestate))				
            elif text == '/gamestate':
                reply(str(gamestate))
            elif text == '/startgame':
                gamestate.give("start")
                reply(str(gamestate))
            elif text == '/y':
                gamestate.give(Vote(1))
                reply(str(gamestate))
            elif text == '/n':
                gamestate.give(Vote(0))
                reply(str(gamestate))
            elif text == '/whatstate':
                reply(gamestate.whatstate())
            else:
                gamestate.give(Player(chat_id, str(text)))
                reply(str(gamestate))

        # CUSTOMIZE FROM HERE
		
		
        elif 'who are you' in text:
            reply('telebot starter kit, created by yukuku: https://github.com/yukuku/telebot')
        elif 'what time' in text:
            reply('look at the corner of your screen!')
        else:
            if getEnabled(chat_id):
				reply(text + " my dear friend")
                #reply('I got your message! (but I do not know how to answer)')
            else:
				reply("you have not enabled this bot")
                #logging.info('not enabled for chat_id {}'.format(chat_id))


app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
], debug=True)
