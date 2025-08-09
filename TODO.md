# Architect's TODO List

This document outlines the proposed architectural changes to improve the Briscola application.

## Phase 1: Backend Refactoring

- [ ] **State Management:**
  - [ ] Create a `state.py` module to encapsulate all in-memory data (e.g., `SOCKET__OID`, `OID__GAME`, `ROOMS`). This will centralize state and make it easier to replace with a more robust solution like Redis in the future.
  - [ ] Refactor `app.py` to import and use the new state management module.

- [ ] **SocketIO Event Handlers:**
  - [ ] Create a `sockets.py` module.
  - [ ] Move all SocketIO event handlers (e.g., `@socketio.on(...)`) from `app.py` to `sockets.py`.
  - [ ] Create a function in `sockets.py` to initialize the socket events, which will be called from `app.py`. This will keep `app.py` cleaner and focused on application setup.

- [ ] **API Endpoints:**
  - [ ] Create an `api.py` module.
  - [ ] Move all Flask API routes (e.g., `@app.route('/api/...')`) from `app.py` to `api.py` using a Flask Blueprint.
  - [ ] Register the Blueprint in `app.py`.

- [ ] **Game Logic:**
  - [ ] The game logic seems reasonably separated in `play/web/client.py` and the `card_games` directory. No major changes are proposed here for now, but we should keep an eye on it as the application grows.

## Phase 2: Frontend Refactoring

- [ ] **JavaScript Modularity:**
  - [ ] Create separate JavaScript files for different functionalities. For example:
    - `lobby.js`: Handles the initial game setup, mode selection, and difficulty.
    - `room.js`: Manages creating, joining, leaving, and waiting in rooms.
    - `game.js`: Contains the logic for the actual game turn page.
    - `websockets.js`: Centralizes all socket event listeners and emitters.
  - [ ] Update `index.html`, `turn.html`, etc., to import these new JavaScript modules.

- [ ] **Template Splitting:**
  - [ ] The current `index.html` serves as both the lobby and the room. We should consider splitting this into `lobby.html` and `room.html`.
  - [ ] Alternatively, we can use a single-page application (SPA) approach where different "views" (lobby, room) are dynamically rendered using JavaScript, hiding and showing different sections of the `index.html` page. The current implementation already does a bit of this, and we can formalize it.

## Phase 3: Long-Term Scalability

- [ ] **Persistent State:**
  - [ ] Replace the in-memory state management with a more persistent solution like Redis. This will allow the application to scale across multiple workers and prevent data loss on server restarts. This is a larger task and should be considered after the initial refactoring.
