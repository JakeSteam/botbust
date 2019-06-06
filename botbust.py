import praw
import os
import re
from collections import deque
import threading
import yaml
import time
import requests

#set globals

try:
    r=praw.Reddit('botbust')
except:
    r=praw.Reddit(client_id=os.environ.get("client_id"),
                  client_secret=os.environ.get("client_secret"),
                  username=os.environ.get("username"),
                  password=os.environ.get("password"),
                  user_agent="modbanner from heroku")

ME = r.user.me()
SUBREDDIT = r.subreddit('BotBust')
LOG_SUB = r.subreddit('BotBustLog')
LOG_TITLE = "/u/{0} banned from /r/{1}"

BAN_NOTE = "BotBusted!"
BAN_MESSAGE = ("Known comment bots are not welcome in /r/{0}"
               "\n\n*[I am a bot, and this action was performed automatically](/r/botbust/about/sticky). "
               "If you wish to dispute your status as a blacklisted comment bot, please "
               "[click here](https://www.reddit.com/message/compose?to=%2Fr%2FBotBust&subject=ban%20dispute:%20{1}).*"
                )
WELCOME_MESSAGE = ("Hello, moderators of /r/{0}"
                   "\n\nI am now helping keep your subreddit free of known worthless comment bots."
                   "\n\nFor more information, or to submit a worthless bot to my banlist, please visit /r/BotBust."
                   )
NSFW_MESSAGE = ("Hello, moderators of /r/{0}"
                "\n\nThank you for your interest in BotBust."
                "\n\nHowever, BotBust is not available for NSFW subreddits. Thank you for understanding.")

DEBARRED_INVITE=("Hello, moderators of /r/{}"
                  "\n\nThank you for using BotBust. However, BotBust will not be serving your subreddit at this time due to the moderator status of the following debarred account(s):"
                  "\n\n{}Debarred individuals are not eligible to benefit from the BotBust service.")

DEBARRED_SUBREDDIT=("/r/{} is banned from using BotBust. Thank you for your interest.")

ALREADY_BANNED='Thank you for submitting to BotBust. The account {} is already on my blacklist. To avoid cluttering the subreddit, this submission has been removed.'
MESSAGE_FORWARD='The following message was sent to {} by /u/{}:\n\n---\n\n{}'


class Bot():

    def __init__(self):

        self.moderated=[]
        self.friends=[]
        self.triggered=deque([],maxlen=100)
        self.checked=deque([],maxlen=200)

    def load_debarments(self):

        self.debarred=yaml.load(r.subreddit('captainmeta4bots').wiki['debar'].content_md)
        for category in self.debarred:
            for entry in category:
                entry=entry.lower()

    def check_all_debarments(self):
        self.load_debarments()

        for sub in r.user.moderator_subreddits(limit=None):
            leave=False
            for mod in sub.moderator():
                    if mod.name in self.debarred['users']:
                        leave=True
            if leave:
                sub.moderator.leave()
                print("Departed {}".format(sub.display_name))

    def debarment_monitoring(self):
        while True:
            print('Checking debarments...')
            self.check_all_debarments()
            print('Done checking debarments. Thread sleeping for 1 hr.')
            time.sleep(3600)
        

    def reload_moderated(self):

        self.moderated=[]

        for subreddit in r.user.moderator_subreddits(limit=None):
            self.moderated.append(subreddit.display_name)

    def reload_friends(self):
        self.friends=[]
        for user in r.user.friends():
            self.friends.append(user.name)


    def run(self):

        debar_thread=threading.Thread(target=self.debarment_monitoring)
        debar_thread.start()

        print('checking mod invites')
        self.check_for_mod_invites()
        print('loading moderated sub list')
        self.reload_moderated()
        print('loading "friend" list')
        self.reload_friends()

        print('beginning loop')
        while True:
            self.check_for_new_banned()
            self.patrol_r_friends()
            self.check_for_mod_invites()

            #self.update_status()

    def update_status(self):

        data={"refresh":"62129581-rY93dhrcdOV9VdcW-KF7Waeqxko"}
        requests.post("https://api.captainmeta4.me/reddit/botbust", data=data)
        
    def check_for_mod_invites(self):

        for message in r.inbox.unread(limit=None):
            message.mark_read()

            #filter out everything but PMs
            if not message.fullname.startswith('t4_'):
                continue

            #filter out everything not sent by a subreddit
            #forward to me
            #if message.author is not None:
                #ignore pms from mod_mailer
            #    if message.author.name in ['mod_mailer']:
            #        continue
            #    r.redditor('captainmeta4').message('Message Forward: {}'.format(message.subject),MESSAGE_FORWARD.format(message.dest,message.author.name,message.body))
            #    continue

            #filter out messages not associated with a subreddit
            if message.subreddit is None:
                continue
            
            try:
                if message.subreddit.over18:
                    message.reply(NSFW_MESSAGE.format(message.subreddit.display_name))
                    continue
            except:
                pass

            try:
                self.load_debarments()
                if message.subreddit.display_name in self.debarred['subreddits']:
                    message.reply(DEBARRED_SUBREDDIT.format(message.subreddit.display_name))
                    continue
            except:
                pass

            try:
                deny=False
                for mod in message.subreddit.moderator():
                    if mod.name in self.debarred['users']:
                        deny=True
                if deny:
                    message.reply("The invitation cannot be accepted with your current mod roster, which includes at least one account that is banned from using BotBust. Thank you for your interest.")
                    continue
            except:
                pass
            
            try:                
                message.subreddit.mod.accept_invite()
                print('accepted invite to /r/'+message.subreddit.display_name)
                self.moderated.append(message.subreddit.display_name)
                self.log_add(message.subreddit.display_name)
            except:
                pass
        
    def patrol_r_friends(self):
        
        #load comments
        
        for comment in r.subreddit('friends').comments(limit=100):

            #All comments here will be by a banned account.
            #the only thing to check is that it's in a moderated subreddit

            if comment.subreddit.display_name not in self.moderated:
                continue

            if comment.banned_by:
                continue

            #ignore comments whose authors are botbustproof
            if comment.author_flair_css_class:
                if "botbustproof" in comment.author_flair_css_class:
                    continue
                    
            #avoid duplicate work
            if comment.id in self.triggered:
                continue

            

            #at this point the ban needs to be issued
            
            # protect against insufficient mod perms by using try
            try:
                comment.mod.remove(spam=True)
            except:
                pass

            print('banning /u/'+comment.author.name+' from /r/'+comment.subreddit.display_name)
            
            try:
                comment.subreddit.muted.add(comment.author, note="BotBusted!")
            except:
                pass
              
            try:
                comment.subreddit.banned.add(comment.author, note="BotBusted!", ban_message = BAN_MESSAGE.format(comment.subreddit.display_name, comment.author.name))
            except:
                pass
            else:
                self.log_ban(comment)
              
            #avoid duplicate work
            self.triggered.append(comment.id)
                      
    def log_add(self, name):
        url="https://reddit.com/r/{}".format(name)
        title="Accepted mod invite to /r/{}".format(name)
        LOG_SUB.submit(title, url=url).mod.approve()
                      
                      
        

    def log_ban(self, comment):

        user = comment.author.name
        sub = comment.subreddit.display_name
        url = "https://reddit.com{}".format(comment.permalink)
        
        title = LOG_TITLE.format(user, sub)

        LOG_SUB.submit(title, url=url).mod.approve()
        
    def check_for_new_banned(self):

        need_to_reload=False

        #process pending check-for-bans. search by flair
        for submission in SUBREDDIT.search("flair:checking", syntax="lucene", limit=None):

            #ignore any stray search results
            if submission.link_flair_css_class !="checkban":
                continue

            #ignore submissions that have been checked already
            if submission.id in self.checked:
                continue

            self.checked.append(submission.id)

            #get the username
            name = re.match("https?://(\w{1,3}\.)?reddit.com/u(ser)?/([A-Za-z0-9_-]+)/?", submission.url).group(3)

            print('checking ban state on /u/'+name)
            
            if name in self.friends:
                #flair the post, remove it, and add an explanatory comment
                submission.mod.flair(text="Already Banned!", css_class="banned")
                submission.mod.remove(spam=True)
                if name.startswith('_'):
                    name='\\'+name
                submission.reply(ALREADY_BANNED.format(name)).mod.distinguish(sticky=True)
                print('/u/'+name+' is already banned')
            else:
                submission.mod.flair(text="For Review", css_class = "exclam")
                print('/u/'+name+' needs moderator review')

        #process pending bans/unbans. search by flair
        for submission in SUBREDDIT.search('flair:pending', syntax="lucene", limit=None):

            #ignore any stray search results
            if submission.link_flair_css_class == "banpending":

                need_to_reload = True

                #get the username
                name = re.match("https?://(\w{1,3}\.)?reddit.com/u(ser)?/([A-Za-z0-9_-]+)/?", submission.url).group(3)

                #friend the redditor
                r.redditor(name).friend()
                print(name+" banned!")
                submission.mod.flair(text="Banned!", css_class="banned")
           
            elif submission.link_flair_css_class == "unbanpending":

                need_to_reload = True

                #get the username
                name = re.match("https?://(\w{1,3}\.)?reddit.com/u(ser)?/([A-Za-z0-9_-]+)/?", submission.url).group(3)

                #unfriend the redditor
                r.redditor(name).unfriend()
                print(name+" unbanned")
                submission.mod.flair(text="Unbanned", css_class="unbanned")

        if need_to_reload:
            self.reload_friends()

if __name__=="__main__":
    b=Bot()
    while True:
        try:
            b.run()
        except Exception as e:
            print(str(e))
        
