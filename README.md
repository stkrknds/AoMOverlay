# AoMOverlay
An overlay for Age of Mythology, that displays the players' ranks, elo, win/losses, streak &amp; winrate. Works only with Voobly(not E.E.).  

Written in Python. The statistics of the players are fetched from the [Voobly API](https://www.voobly.com/pages/view/147/External-API-Documentation), using asynchronous requests(with the aiohttp & asyncio modules), while the GUI of the application was made using the QT6(PyQT6) framework. 

## Voobly API Key
In order to use this application, you need to obtain a [Voobly API Key](https://www.voobly.com/pages/view/27/Developer-Membership-Types) and place it in line 6 of the file data.py.

## Credits
To prominent member of the AoM community, [DarthRevan24](https://liquipedia.net/ageofempires/DarthRevan24), for coming up with the idea.

This overlay was inspired by another great overlay made for Age of Empires 4 by [aoe4world](https://github.com/aoe4world/overlay).
