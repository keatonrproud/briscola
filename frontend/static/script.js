import { socket } from '/static/js/websocket.js'; // Import socket instance
export { updateGameState, checkIfInGame };

function getCardPath() {
    return navigator.onLine
    ? 'https://s3.eu-north-1.amazonaws.com/briscola.pro/piacentine/piacentine'
        : '/static/piacentine';
}

function setCardImage(cardDiv, card) {
    if (card && card.number && card.suit) {

        let cardFileName = `${card.number.name}_${card.suit.name}.png`.toLowerCase();
        let cardUrl = `${getCardPath()}/${cardFileName}`;

        cardDiv.style.backgroundImage = `url(${cardUrl.toLowerCase()})`;
        cardDiv.style.backgroundSize = 'contain';
        cardDiv.style.backgroundRepeat = 'no-repeat';
        cardDiv.style.backgroundPosition = 'center';
    } else {
        console.error('Card data is invalid:', card);
    }
}

function getGameState(continue_play=false) {
    socket.emit("get_state", {continue_play: continue_play});
}

function updateCards(players, shownPlayer, cardsPlayable) {
    const playerCount = players.length;

    const playerCardsContainer = document.getElementById('player-cards');
    const oppCardsContainer = document.getElementById('opp-cards');
    const leftPlayerCardsContainer = document.getElementById('left-player-cards');
    const rightPlayerCardsContainer = document.getElementById('right-player-cards');

    // Clear all card containers first
    playerCardsContainer.innerHTML = '';
    oppCardsContainer.innerHTML = '';
    if (leftPlayerCardsContainer) leftPlayerCardsContainer.innerHTML = '';
    if (rightPlayerCardsContainer) rightPlayerCardsContainer.innerHTML = '';
    
    // Remove all existing player name displays
    document.querySelectorAll('.player-name-display').forEach(el => {
        if (el.parentNode) {
            el.parentNode.remove();
        }
    });


    // Render shown player's cards
    shownPlayer.hand.cards.forEach((card) => {
        const cardDiv = document.createElement('div');
        setCardImage(cardDiv, card);
        
        // Set appropriate cursor style and class based on playability
        if (cardsPlayable) {
            cardDiv.className = 'card playable';
            cardDiv.style.cursor = 'pointer';
            
            function handleCardClick(event) {
                const cardIndex = Array.from(playerCardsContainer.children).indexOf(cardDiv);
                // Cards are already checked to be playable when event listeners are attached
                playHumanCard(cardIndex, cardDiv);
            }
            
            cardDiv.addEventListener('click', handleCardClick);
            cardDiv.handleCardClick = handleCardClick;
        } else {
            cardDiv.className = 'card not-playable';
            // Add subtle visual indicator that card is not playable
            cardDiv.style.opacity = '0.8';
        }
        
        playerCardsContainer.appendChild(cardDiv);
    });
    
    // Get the username for the shown player
    let username;
    
    // Debug shownPlayer object
    console.log(`Trying to get username for shown player:`, shownPlayer);
    
    // First try to get from game state if it's an online game
    if (currentGameState && currentGameState.player_usernames && shownPlayer.player_num) {
        const playerNum = shownPlayer.player_num.toString();
        console.log(`Looking up shown player username for player ${playerNum} in:`, currentGameState.player_usernames);
        username = currentGameState.player_usernames[playerNum];
        console.log(`Username found from game state for shown player: ${username || 'none'}`);
    }
    
    // If not found and this is the current player, use localStorage
    if (!username && shownPlayer.player_num === 1) {
        username = localStorage.getItem('username');
        console.log(`Username from localStorage: ${username || 'none'}`);
    }
    
    // Default to a readable name if no username is available
    if (!username) {
        if (shownPlayer.is_person) {
            username = `Player ${shownPlayer.player_num}`;
        } else {
            // For computers, use sequential numbering instead of player number
            // Find all computer players in the game
            const computerPlayers = currentGameState.players.filter(p => !p.is_person);
            // Find the index of this computer player among all computer players
            const computerIndex = computerPlayers.findIndex(p => p.player_num === shownPlayer.player_num);
            // Use 1-based indexing for display
            username = `Computer ${computerIndex + 1}`;
            console.log(`Using computer index ${computerIndex + 1} for shown player ${shownPlayer.player_num}`);
        }
        console.log(`Using default username for shown player: ${username}`);
    }
    
    // Don't display the current player's username - they know who they are
    console.log("Current player's username:", username, "(not displaying)");

    // Helper function to add username display for a player
    function addPlayerNameDisplay(player, containerEl, position = 'top') {
        // Get username for this player
        let playerUsername;
        
        // Debug player object
        console.log(`Trying to get username for player:`, player);
        
        // Try to get from game state if online game
        if (currentGameState && currentGameState.player_usernames && player.player_num) {
            const playerNum = player.player_num.toString();
            console.log(`Looking up username for player ${playerNum} in:`, currentGameState.player_usernames);
            playerUsername = currentGameState.player_usernames[playerNum];
            console.log(`Username found from game state: ${playerUsername || 'none'}`);
        }
        
        // Default name if no username found
        if (!playerUsername) {
            if (player.is_person) {
                playerUsername = `Player ${player.player_num}`;
            } else {
                // For computers, use sequential numbering instead of player number
                // Find all computer players in the game
                const computerPlayers = currentGameState.players.filter(p => !p.is_person);
                // Find the index of this computer player among all computer players
                const computerIndex = computerPlayers.findIndex(p => p.player_num === player.player_num);
                // Use 1-based indexing for display
                playerUsername = `Computer ${computerIndex + 1}`;
                console.log(`Using computer index ${computerIndex + 1} for player ${player.player_num}`);
            }
            console.log(`Using default username: ${playerUsername}`);
        }
        
        // Create name display
        const nameContainer = document.createElement('div');
        nameContainer.style.width = '100%';
        nameContainer.style.textAlign = 'center';
        nameContainer.style.margin = position === 'top' ? '0 0 10px 0' : '10px 0 0 0';
        nameContainer.style.position = 'relative';
        nameContainer.style.zIndex = '100'; // Higher z-index to appear above cards
        
        const nameDisplay = document.createElement('div');
        nameDisplay.className = 'player-name-display';
        nameDisplay.textContent = playerUsername;
        nameDisplay.style.display = 'inline-block';
        nameDisplay.style.backgroundColor = 'rgba(0, 0, 0, 0.7)'; // Slightly darker for better contrast
        nameDisplay.style.color = 'white';
        nameDisplay.style.padding = '3px 8px';
        nameDisplay.style.borderRadius = '4px';
        nameDisplay.style.fontSize = '0.9rem';
        nameDisplay.style.fontWeight = 'bold';
        nameDisplay.style.zIndex = '100'; // Ensure name is above cards
        
        nameContainer.appendChild(nameDisplay);
        
        // Add to container based on position
        if (position === 'top') {
            containerEl.parentNode.insertBefore(nameContainer, containerEl);
        } else {
            containerEl.parentNode.insertBefore(nameContainer, containerEl.nextSibling);
        }
        
        return playerUsername;
    }

    // Render other players' cards (face down)
    if (playerCount === 2) {
        const oppPlayer = players.find(p => p.player_num !== shownPlayer.player_num);
        
        // Add opponent's name at the top of their cards
        addPlayerNameDisplay(oppPlayer, oppCardsContainer, 'top');
        
        oppPlayer.hand.cards.forEach(() => {
            const oppCardDiv = document.createElement('div');
            oppCardDiv.className = 'card';
            oppCardsContainer.appendChild(oppCardDiv);
        });
    } else if (playerCount === 4) {
        const shownPlayerIndex = players.findIndex(p => p.player_num === shownPlayer.player_num);
        if (shownPlayerIndex === -1) {
            return;
        }
        const partnerPlayer = players[(shownPlayerIndex + 2) % 4];
        const leftPlayer = players[(shownPlayerIndex + 3) % 4];
        const rightPlayer = players[(shownPlayerIndex + 1) % 4];

        // Add opponent names
        addPlayerNameDisplay(partnerPlayer, oppCardsContainer, 'top');
        addPlayerNameDisplay(leftPlayer, leftPlayerCardsContainer, 'top');
        addPlayerNameDisplay(rightPlayer, rightPlayerCardsContainer, 'top');
        
        partnerPlayer.hand.cards.forEach(() => {
            const cardDiv = document.createElement('div');
            cardDiv.className = 'card';
            oppCardsContainer.appendChild(cardDiv);
        });

        leftPlayer.hand.cards.forEach(() => {
            const cardDiv = document.createElement('div');
            cardDiv.className = 'card vertical';
            leftPlayerCardsContainer.appendChild(cardDiv);
        });

        rightPlayer.hand.cards.forEach(() => {
            const cardDiv = document.createElement('div');
            cardDiv.className = 'card vertical';
            rightPlayerCardsContainer.appendChild(cardDiv);
        });
    }
}

function updateTurnInfo(player, shownPlayer, gameState) {
    const turnInfo = document.getElementById('turn-info');
    
    // Check if turn info element exists
    if (!turnInfo) return;

    let text = "";
    let singleHuman = gameState.table_settings.player_count - gameState.table_settings.computer_count === 1;
    
    // Store previous turn state for comparison
    const prevTurnText = turnInfo.textContent;
    const isYourTurnNow = player.player_num === shownPlayer.player_num && (gameState.online || singleHuman);
    const wasYourTurnBefore = prevTurnText.includes('Your Turn');
    
    // Check if this is an online game
    const isOnlineGame = gameState.online === true;
    
    // If it's the current player, use "Your Turn"
    if (isYourTurnNow) {
        text = `${player.color} Your Turn`;
    } 
    // For other human players in online games, show their username
    else if (player.is_person && isOnlineGame) {
        // Get username for the active player
        let playerUsername = null;
        
        // Try to get from game state
        if (gameState.player_usernames && player.player_num) {
            const playerNum = player.player_num.toString();
            playerUsername = gameState.player_usernames[playerNum];
        }
        
        // If we have a username, use it
        if (playerUsername) {
            text = `${player.color} ${playerUsername}'s Turn`;
        } 
        // Otherwise fall back to Player X
        else {
            text = `${player.color} Player ${player.player_num}'s Turn`;
        }
    } 
    // For local games with other human players (rare case)
    else if (player.is_person) {
        text = `${player.color} Player ${player.player_num}'s Turn`;
    }
    // For computer players, use sequential numbering
    else {
        // For computers, use sequential numbering instead of player number
        if (gameState.players) {
            // Find all computer players in the game
            const computerPlayers = gameState.players.filter(p => !p.is_person);
            // Find the index of this computer player among all computer players
            const computerIndex = computerPlayers.findIndex(p => p.player_num === player.player_num);
            // Use 1-based indexing for display
            text = `${player.color} Computer ${computerIndex + 1}'s Turn`;
        } else {
            text = `${player.color} Computer's Turn`;
        }
    }
    
    // Add visual highlight effect if it just became your turn
    if (isYourTurnNow && !wasYourTurnBefore) {
        // Apply highlight animation
        turnInfo.classList.add('highlight-turn');
        setTimeout(() => {
            turnInfo.classList.remove('highlight-turn');
        }, 2000);
        
        // Play notification sound if supported
        try {
            const audio = new Audio('data:audio/mp3;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA/+M4wAAAAAAAAAAAAEluZm8AAAAPAAAAAwAAAbAAzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzMzM//////////////////////////////////////////////////////////////////8AAAAATGF2YzU4LjEzAAAAAAAAAAAAAAAAJAZFgAAAAAAABsAAAAAAAAAAAAAAAP/jWMQACwALLDvrxC/VAPT+/sdtfigZ/uneLvPQLfJ/9e4FG0FQQhms0LBEARdX1tT661///9XV+LVVU5PABMgAIoAHuJ90oxnqZyucChGhIIANvBf/KAgEDUIIWZzo1LFui/JkXoVEIIJzneZQz/lz/KHs6/Wf/yh9C+XQfjKFuqpdnZ3NHxpcqgAEsAEn5NtGfhf/Lc/C/KX8zoiIRVXh8RaoiwzVW+mf/6oBiFAEQAALuKWwbtix7bNuxPttg0pRGm3RBtSxbT9VW227c3bnpQAGMAEVgAVg+TAYP3+Kig6iMtX/+UdHEVFR/lKjqK/9R1FfyoqOoqP//X////qKj+VHX//qKioqKn8qKioqKio+o6ioqP////iQAVQARIAfYUDf6P//+TOkyD//5M/kz+v//6aoADcAEJIAGMPkwpP//8jIywxJkf/+TMjLDLlSMuVOVP/P5cyMyUYnE5Wyp/9b//P9JGXPeTM/8mZF5M5UyMyU//8mZKo');
            audio.play();
        } catch(e) {
            console.log('Sound not supported or blocked by browser');
        }
    }

    // Add styles to the turn info element based on whose turn it is
    turnInfo.textContent = text;
    
    // Always keep text white, just change the font weight for emphasis
    if (isYourTurnNow) {
        turnInfo.style.fontWeight = 'bold';
    } else {
        turnInfo.style.fontWeight = 'normal';
    }
    
    // Use the CSS positioning to ensure proper centering
    // For large screens, the CSS will handle positioning with absolute and transform
}

// Store current game state globally to access player usernames
let currentGameState = null;

// Helper function to handle player display formatting
function formatPlayerDisplay(player) {
    if (!player) return "";
    
    // First check if we have username info in the game state
    if (currentGameState && currentGameState.player_usernames && player.player_num) {
        const playerNum = player.player_num.toString();
        if (currentGameState.player_usernames[playerNum]) {
            return `${player.color} ${currentGameState.player_usernames[playerNum]}`;
        }
    }
    
    // If this is the current player and we have a local username, use that
    const username = localStorage.getItem('username');
    // Only use for the current player in local games
    if (username && !currentGameState?.online && player.player_num === 1) {
        return `${player.color} ${username}`;
    }
    
    // Check for enum patterns in repr and fix them
    if (player.repr) {
        // If contains "PlayerType.HUMAN" or "PlayerType.COMPUTER", extract just the value
        if (player.repr.includes('PlayerType.HUMAN')) {
            const cleanRepr = player.repr.replace('PlayerType.HUMAN', 'Human');
            return cleanRepr;
        }
        if (player.repr.includes('PlayerType.COMPUTER')) {
            const cleanRepr = player.repr.replace('PlayerType.COMPUTER', 'Computer');
            return cleanRepr;
        }
        // If no specific enum patterns but doesn't include TeamName, use as is
        if (!player.repr.includes('TeamName.')) {
            return player.repr;
        }
    }
    
    // Otherwise construct a display name from available properties
    if (player.is_person) {
        return `${player.color} Human ${player.player_num}`;
    } else {
        // For computers, use sequential numbering instead of player number
        if (currentGameState && currentGameState.players) {
            // Find all computer players in the game
            const computerPlayers = currentGameState.players.filter(p => !p.is_person);
            // Find the index of this computer player among all computer players
            const computerIndex = computerPlayers.findIndex(p => p.player_num === player.player_num);
            // Use 1-based indexing for display
            return `${player.color} Computer ${computerIndex + 1}`;
        }
        // Fallback if we can't determine the computer index
        return `${player.color} Computer ${player.player_num}`;
    }
}

function updateBriscolaCard(card, num_cards_in_deck) {
    const briscolaCard = document.getElementById('briscola-card');

    if (briscolaCard) {
        if (card) {
            if (num_cards_in_deck > 0) {
                setCardImage(briscolaCard, card);
            } else {
                briscolaCard.style.backgroundImage = '';
                briscolaCard.querySelector('.symbol').textContent = card.suit.symbol;
                briscolaCard.querySelector('.number').textContent = '';
            }
        } else {
            briscolaCard.querySelector('.symbol').textContent = '';
            briscolaCard.querySelector('.number').textContent = '';
        }
    } else {
        console.error('Briscola card element not found');
    }
}


function setUpInGameResultListener() {

    if (!socket.__inGameResultSetUp) {
        // Listen for the response from the server
        socket.on('in_game_check_result', async (data) => {
            if (!data.in_game) {
                window.location.href = '/';
                }
            }
        )
        socket.__inGameResultSetUp = true;
    }}

async function checkIfInGame() {
    const userId = localStorage.getItem('user_id');
    await socket.emit("update_user_id", { user_id: userId});

    setUpInGameResultListener();
    socket.emit("check_if_in_game");
}

function setUpHumanCardPlayedListener() {
    // Remove existing listener if it exists
    socket.off('active_card_played');

    // Listen for the response from the server
    socket.on('active_card_played', async (data) => {
        console.log('Card played event received:', new Date().toLocaleTimeString());
        if (!data.active_player.is_person) {
            return;
        }

        await getGameState();

        if (data.pile.cards.length === data.players.length) {
            setTimeout(() => {
                endPlay();
            }, 1500);
        } else {
            endPlay();
        }
    });

    socket.__humanCardPlayedSetUp = true;
}

function makeShownCardsUnplayable() {
    const playerCardsContainer = document.getElementById('player-cards');
    Array.from(playerCardsContainer.children).forEach(cardDiv => {
        cardDiv.removeEventListener('click', cardDiv.handleCardClick);
        delete cardDiv.handleCardClick;
    })
}

async function playHumanCard(cardIndex, cardDiv) {
    makeShownCardsUnplayable();
    
    // Add animation class
    cardDiv.classList.add('played');
    
    // After a short delay, set up the listener and emit the card play event
    setTimeout(() => {
        setUpHumanCardPlayedListener();
        socket.emit('play_active_card', { card_index: cardIndex });
    }, 500);
}

async function getComputerChoice() {
    try {
        const response = await fetch('/api/get_computer_choice', {method: 'POST', headers: {
        'Content-Type': 'application/json'},body: JSON.stringify({ socket_id: socket.id })})
        const res = await response.json();
        return res.card_idx;
    } catch (error) {
        console.error('Error:', error);
    }
}

function setUpComputerCardPlayedListener() {
    // We don't need a separate computer card played listener
    // since we've already improved the main active_card_played listener
    socket.__computerCardPlayedSetUp = true;
}

async function playComputerCard(cardIndex) {
    setUpComputerCardPlayedListener();
    socket.emit('play_active_card', {card_index: cardIndex});
}

function endPlay() {
    socket.emit("end_play");
}

async function playComputerTurn(slow=false) {
    // get their choice
    const computerChoice = await getComputerChoice();

    // play their card and update state
    const oppCardsContainer = document.getElementById('opp-cards');
    const oppCardDiv = Array.from(oppCardsContainer.children).indexOf(computerChoice);

    setTimeout(async () => {
        await playComputerCard(computerChoice, oppCardDiv);

        // if slow, it's to give time to see the cards before getting pulled away
        // when not slow, it's because a player's turn is next
        if (slow) {
            setTimeout(() => {endPlay();}, 1500)
        } else {setTimeout(() => {endPlay();}, 500);}
    }, 1000)
}


function showConfetti(xOrigin, yOrigin) {
    // Simple confetti burst
    confetti({
        particleCount: 50,  // Number of confetti particles
        spread: 50,          // Spread angle
        origin: { x: xOrigin, y: yOrigin }
    });
}

let pastScores = {};
function updateScoreboard(players, teams) {
    const scoresContainer = document.getElementById('scores');
    if (!scoresContainer) return; // Exit if container not found
    
    scoresContainer.innerHTML = ''; // Clear existing scores
    const teamScoresContainer = document.getElementById('team-scores');
    if (teamScoresContainer) {
        teamScoresContainer.innerHTML = '';
    }

    if (teams) {
        teams.forEach(team => {
            const teamScoreDiv = document.createElement('div');
            teamScoreDiv.className = 'score';
            
            // Format team name properly
            let teamName = team.name;
            if (typeof teamName === 'string' && teamName.includes('TeamName.')) {
                teamName = teamName.split('.').pop(); // Extract name from enum
            }
            
            teamScoreDiv.innerHTML = `
                <span>Team ${teamName}:</span>
                <span>${team.score}</span>
            `;
            if (teamScoresContainer) {
                teamScoresContainer.appendChild(teamScoreDiv);
            }
        });
    }

    if (players && Array.isArray(players)) {
        players.forEach(player => {
            if (!player) return;
            
            const scoreDiv = document.createElement('div');
            scoreDiv.className = 'score';
            scoreDiv.innerHTML = `
                <span>${formatPlayerDisplay(player)}:</span>
                <span>${player.score}</span>
            `;
            scoresContainer.appendChild(scoreDiv);

            pastScores[player.player_num] = player.score;
        });
    }
    
    // Make scoreboard visible
    const scoreboardContainer = document.getElementById('scoreboard-container');
    if (scoreboardContainer) {
        scoreboardContainer.style.display = 'block';
    }
}

function updateDeck(cards) {
    const deckContainer = document.getElementById('deck-container');
    deckContainer.innerHTML = ''; // Clear existing deck

    var cardNum = cards.length;

    // less by 1 because the Briscola card is already shown
    for (let i = 0; i < cardNum; i++) {
        const cardDiv = document.createElement('div');
        cardDiv.className = 'deck-card';
        cardDiv.innerHTML = `
            <div class="number">${cardNum}</div>
        `;

        // Card face-down (no symbol or number)
        deckContainer.appendChild(cardDiv);
    }
}

function updateActivePile(cards, activePlayer, shownPlayer) {
    const activePileContainer = document.getElementById('active-pile');

    if (!activePileContainer) {
        console.error('Active pile element not found');
        return;
    }

    // Reset the transformation styles before adding any new ones
    activePileContainer.style.transition = 'none'; // Disable transitions to reset styles
    activePileContainer.style.transform = 'translate(-50%, -50%) translateY(0)'; // Center element without shifting
    activePileContainer.style.opacity = '1'; // Ensure it's fully visible to start

    if (cards.length === 0) {

        const animationDirection = (activePlayer.player_num === shownPlayer.player_num) ? 'down' : 'up';

        activePileContainer.classList.add('cleared', `move-${animationDirection}`);

        // Use a timeout to remove the class after the animation ends
        setTimeout(() => {
            activePileContainer.classList.remove('cleared', `move-${animationDirection}`);
            activePileContainer.innerHTML = ''; // Clear existing cards after animation
        }, 1000); // Match the duration of the animation (0.5s)

        cards.forEach(card => {
            const cardDiv = document.createElement('div');
            cardDiv.className = 'card';
            activePileContainer.appendChild(cardDiv);

            setCardImage(cardDiv, card);
        });

    } else {
        activePileContainer.innerHTML = ''; // Clear existing cards immediately
        cards.forEach(card => {
            const cardDiv = document.createElement('div');
            cardDiv.className = 'card';
            activePileContainer.appendChild(cardDiv);

            setCardImage(cardDiv, card);
        });}

}




function endGame() {
    window.location.href = '/end_game';
}

function blastConfettiForBigScore() {
    const scoreboard = document.getElementById('scoreboard');
    const rect = scoreboard.getBoundingClientRect();
    const x = rect.left + rect.width / 2; // Horizontal center of the scoreboard
    const y = rect.top; // Top of the scoreboard

    showConfetti(x / window.innerWidth,  y / window.innerHeight);
}

async function updateGameState(data) {
    // Extract data for the active player
    const state = data.game_state;
    
    // Check if we got a valid state
    if (!state || !state.active_player) {
        console.error('Invalid game state received:', data);
        return;
    }

    // Store the game state for username access
    currentGameState = state;
    
    const activePlayer = state.active_player;
    const playerNum = activePlayer.player_num;
    
    // Debug entire game state
    console.log('Full game state:', JSON.parse(JSON.stringify(state)));
    
    // Debug log player usernames if available
    if (state.player_usernames) {
        console.log('Player usernames:', state.player_usernames);
    }

    if (activePlayer.score - (pastScores[playerNum] || 0) > 11) {
        blastConfettiForBigScore()
    }

    updateBriscolaCard(state.briscola.card, state.deck.current_cards.length); // Update the Briscola card
    updateScoreboard(state.players, state.teams); // Update scoreboard
    updateDeck(state.deck.current_cards); // Update the deck

    let shownPlayer = state.shown_player;
    // is shown player is not fixed, and the active player is a person
    if (!state.online && state.table_settings.computer_count === 0 && activePlayer.is_person) {
        shownPlayer = activePlayer;
    } else if (state.online) {
        try {
            const response = await fetch('/api/convert_socketid_to_oid', {method: 'POST', headers: {
            'Content-Type': 'application/json'},body: JSON.stringify({ socket_id: socket.id })})
            const res = await response.json();
            shownPlayer = state.players[state.userid_playernum_map[res.oid]];
        } catch (error) {
            console.error('Error:', error);
        }
    }

    // cards are playable only if it's currently the shown player's turn, or if not all players have played yet
    const cardsPlayable = shownPlayer.player_num === activePlayer.player_num && state.pile.cards.length !== state.players.length;
    updateCards(state.players, shownPlayer, cardsPlayable);

    updateTurnInfo(activePlayer, shownPlayer, state); // Update the turn info
    updateActivePile(state.pile.cards, activePlayer, shownPlayer); // Update active pile

    const n_cards_played = state.pile.cards.length;
    if (n_cards_played < state.players.length) {
        const isActivePlayersTurn = state.turn_order[n_cards_played].player_num === activePlayer.player_num;
        const activePlayerIsComputer = !activePlayer.is_person;

        if (activePlayerIsComputer && isActivePlayersTurn){
            await playComputerTurn(state.turn_order[state.turn_order.length-1].player_num === activePlayer.player_num);
        }
    }

    if (!state.game_ongoing) {
        endGame();
    }
}

// Handle visibility changes - get current state when tab becomes visible
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && window.location.pathname === '/turn') {
        // Get the state immediately when tab becomes visible
        getGameState();
    }
});

function pingServer() {
    fetch('/keep-alive')
        .then(response => {
            if (response.ok) {
            } else {
                console.error('Ping failed:', response.statusText);
            }
        })
        .catch(error => {
            console.error('Error during ping:', error);
        });
}

// Ping the server every 5 minutes (300000 milliseconds)
setInterval(pingServer, 700000);
