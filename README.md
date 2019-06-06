# BotBust

BotBust is a bot that hunts down known useless comment bots, removes their comments, and bans them from the subreddit. It also issues a modmail mute at the same time, to prevent the bot from generating an automated reply and cluttering subreddit modmail.

# What bots are banned?

If there's a link to that bot's profile in [/r/BotBust](https://reddit.com/r/botbust) with a flair of "Banned!" then that bot is on the banlist. This isn't a witch-hunt but a tool for mods to eliminate worthless bots from across all their subreddits without having to ban them in each.

Bots that are eligible to be banned:

* Comments or posts uninvited.
* Provides no value to the community.
* Or just don't work correctly.

Bots that are not eligible to be banned:

* Service/info bots providing wanted information within a "home territory" of one or more specific subreddits related to its subject matter. For example, the card lookup bot in /r/hearthstone.
* Service/info bots that must be explicitly summoned (by a human) in order to respond.
* Moderation assistance bots.
* AutoModerator. 

# Who decides?

The moderators of [/r/BotBust](https://reddit.com/r/botbust). If you think we've made a huge mistake, please [message the moderators](https://www.reddit.com/message/compose?to=%2Fr%2FBotBust).

# Can this be used to ban regular users?

It *could* but it *won't*. The code that runs the bot has no idea if it's banning a user or a bot - it only targets the accounts that it's instructed to target. However, /u/BotBust will only ever be used to exclusively target bots. The banning of human users should always be left up to the mods that run that subreddit, not any sort of shared list.

# I found a bot that should be banned. What do I do?

Make a post in [/r/BotBust](https://reddit.com/r/botbust) linking to its user profile. The mods will review it.

# I want /u/BotBust watching my sub!

Add it as a moderator (only 'access' and 'posts' permissions are required). If your subreddit is SFW, the bot will accept the invite and go to work immediately.

To allow BotBust to issue modmail mutes, also give it 'mail' permissions.

# How long does it take for the bot to work?

Should be under 30 seconds in nearly every case. 

# Where is /u/BotBust currently being used?

Over 800 subreddits. See [its profile](https://www.reddit.com/user/botbust/) for a full list. 

# You banned a bot that I want in my subreddit.

If you want to exempt a bot account from being banned in your subreddit, just add `botbustproof` to its user flair class. This will tell BotBust to ignore it. As long as user flairs are enabled in your subreddit, BotBust will see the `botbustproof` flair and ignore it.

# Developer Guidelines

If, like me, you enjoy writing bots, following these guidelines will help prevent your bot from getting blacklisted.

Bots should:

* Not be repetitive.
* Provide a useful service.
* Stay within a limited number of relevant subreddits OR only respond when explicitly called (by name) by a human.
* Not make excessive use of bold, all-caps, and header formatting.
* Not make walls of text.
