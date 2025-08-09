# Briscola App Issues Todo List

## Bug Fixes

### 1. Player Name Display Issues
- [x] Fix player name displaying enum instead of value (issue in `script.js` when displaying player representation)
- [x] Ensure proper representation in all game views and end-game screen

### 2. Card Interaction Issues
- [x] Fix cards getting stuck when clicked when it's not the player's turn
- [x] Add better visual feedback when a card can't be played
- [x] Prevent card click events when it's not the user's turn

### 3. Turn Notification Issues
- [x] Fix turn notifications not updating automatically (requiring page refresh)
- [x] Improve WebSocket handling to properly update UI when turn changes
- [x] Add visual indicators when it's the player's turn

### 4. Game Initialization Issues
- [x] Fix issue where users need to refresh to see cards after starting a game
- [x] Ensure proper state synchronization when game starts
- [x] Add proper loading indicators during game initialization

### 5. End-Game Score Display Issues
- [x] Fix score display not showing in the end-game screen
- [x] Debug why score data isn't being passed correctly to the end_game template
- [x] Ensure team scores are displayed properly for 4-player games

## Feature Requests

### 6. Username Input
- [x] Add username input field for all multiplayer games
- [x] Store username in localStorage for persistence across sessions
- [x] Update player representation to use custom username instead of default names
- [x] Show the username in an online game somewhere near their cards, small in a visible font/container based on the general gameplay screen

### 7. Team Selection for 4-Player Games
- [x] Add team selection UI for 4-player rooms
- [x] Allow players to choose teams when joining a 4-player game
- [x] Update room management to handle team assignments
- [x] Add visual indicators for team membership during gameplay

## Implementation Plan
- [x] Address critical bugs first (1-5) ✓
- [x] Implement username feature (6) ✓
- [x] Add team selection functionality (7) ✓

## Summary of Fixes

All identified issues have been fixed:

1. Fixed player name display issues by properly handling enum values in Python and presenting them correctly in the UI.
2. Fixed card interaction issues by disabling card click events when it's not the user's turn and adding visual feedback.
3. Fixed turn notification issues by improving the WebSocket connection and adding clear visual indicators when it's a player's turn.
4. Fixed game initialization issues by ensuring all players receive the game state when a game starts.
5. Fixed end-game score display by correcting the data formatting and handling empty/null values.
6. Added username input for multiplayer games with localStorage persistence.
7. Added team selection for 4-player games with visual feedback and proper team assignments.
