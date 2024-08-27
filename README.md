## 🃏    Briscola, open-source, for the terminal and web    🃏

Play vs a friend (local or online!) or the computer at www.briscola.pro ⚔️



---



### TODO List
- Sockets
  - [ ] Room count is accurate at all times and accounts for disconnects
  - [ ] Multiple rooms available, or implement logic for random selection within the room

- In-Game
  - Logic
  - [ ] Exit game button that returns home
  - [ ] Handle disconnect functionality for online multiplayer
    - Attempt to reconnect with a warning popup, after ~X sec then end game
  - Appearance
    - [ ] Wait for cards, etc to load before showing objects on game screen
    - [ ] Fix card image alignment
    - [ ] Briscola card under the deck?
    - [ ] Friendly for small screens, ie mobile
    - [ ] Choice of card set (Piacentine, etc)
    - [ ] Confetti only for the winning player in online multiplayer

- Site Improvements
  - [ ] Small link to the repo on the home screen
  - [ ] Workaround for Render's free tier timeout of ~15min inactivity
  - [ ] If user is not in a game, via USER_LOCAL_GAME or USER_ROOM, then return them home from /turn or /end_game
  - [ ] Signed URL for S3 bucket
