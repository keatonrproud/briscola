## 🃏    Briscola, open-source, for the terminal and web    🃏

Play vs a friend (local or online!) or the computer at www.briscola.pro ⚔️



---



### TODO List
- [ ] Sockets
  - [ ] Multiple rooms available, or implement logic for random selection within the room
  - [ ] Create method for removing players from the game + room (used for disconnects, exit game button, end of game, etc)
    - Remove them from the existing room
    - Return to the home page as default, or to `end_game` for a disconnect
  - [ ] Room count is accurate at all times and **accounts for disconnects**

- [ ] In-Game
  - [ ] Logic
    - [ ] Refresh page causes the game to freeze / have issues... how to avoid this?
    - [ ] If H2H Local, should say player's name instead of always Your Turn
    - [ ] Can't force end_game -- should check some logic, and only if it's valid should it go to end_game, otherwise keep user where they are
    - [ ] If users are in an online game, they shouldn't show in the userCount for users not in a game yet
    - [ ] Improve computer logic
    - [ ] Score should say Computer, if it's a Computer, instead of Player 2
      - [ ] Include player color in scoreboard
    - [ ] If just two people (player vs computer) should say Player and Computer everywhere w/o the numbers
    - [ ] Currently in H2H local, second player can play while pile is being selected. Shouldn't be playable if pile.length === players.length
    - [ ] Handle disconnect functionality for online multiplayer / page refresh
      - Attempt to reconnect with a warning popup, after ~X sec then end game and/or return home
    - [x] Remove Briscola image once it's been drawn, then just show the icon
    - [x] Exit game button that returns home
    - [x] If quickly, player can play >1 card per turn...
    - [x] Make sure `end_game` works as expected
  - [ ] Appearance
    - [ ] First card played by Human in game doesn't show?
    - [ ] Fix card image alignment
    - [x] Briscola card under the deck?
    - [ ] Choice of card set (Piacentine, etc)
    - [x] Short loading screen before match shows up to avoid empty cards, objects, etc
    - [x] Friendly for small screens, ie mobile
      - [x] Home screen
      - [x] Turn screen
      - [x] End Game screen
    - [x] Logic for offline use to load images locally

- [x] Site Improvements
  - [x] Workaround for Render's free tier timeout of ~15min inactivity
  - [x] If user is not in a game, via USER_LOCAL_GAME or USER_ROOM, then return them home from /turn or /end_game
  - [x] Small link to the repo on the home screen
