## 🃏    Briscola, open-source, for the terminal and web    🃏

Play vs a friend (local or online!) or the computer at www.briscola.pro ⚔️



---



### TODO List
- Sockets
  - [ ] Multiple rooms available, or implement logic for random selection within the room
  - [ ] Create method for removing players from the game + room (used for disconnects, exit game button, end of game, etc)
    - Remove them from the existing room
    - Return to the home page as default, or to `end_game` for a disconnect
  - [x] Room count is accurate at all times and accounts for disconnects

- In-Game
  - Logic
  - [ ] H2H local is now broken and doesn't change turns..?
  - [ ] Handle disconnect functionality for online multiplayer / page refresh
    - Attempt to reconnect with a warning popup, after ~X sec then end game and/or return home
  - [ ] Refresh page causes the game to freeze / have issues... how to avoid this?
  - [x] Exit game button that returns home
  - [x] If quickly, player can play >1 card per turn...
  - [x] Make sure `end_game` works as expected
  - Appearance
    - [ ] First card played by Human in game doesn't show?
    - [ ] Fix card image alignment
    - [ ] Briscola card under the deck?
    - [ ] Friendly for small screens, ie mobile
    - [ ] Choice of card set (Piacentine, etc)
    - [ ] Short loading screen before match shows up to avoid empty cards, objects, etc
    - [x] Logic for offline use to load images locally

- Site Improvements
  - [ ] Workaround for Render's free tier timeout of ~15min inactivity
  - [x] If user is not in a game, via USER_LOCAL_GAME or USER_ROOM, then return them home from /turn or /end_game
  - [x] Small link to the repo on the home screen
