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
    
    // Add player name display above cards
    const username = localStorage.getItem('username');
    if (username) {
        const nameDisplay = document.createElement('div');
        nameDisplay.className = 'player-name-display';
        nameDisplay.textContent = username;
        nameDisplay.style.position = 'absolute';
        nameDisplay.style.bottom = '110%';
        nameDisplay.style.left = '50%';
        nameDisplay.style.transform = 'translateX(-50%)';
        nameDisplay.style.backgroundColor = 'rgba(0, 0, 0, 0.6)';
        nameDisplay.style.color = 'white';
        nameDisplay.style.padding = '2px 8px';
        nameDisplay.style.borderRadius = '4px';
        nameDisplay.style.fontSize = '0.9rem';
        nameDisplay.style.zIndex = '5';
        playerCardsContainer.style.position = 'relative';
        playerCardsContainer.appendChild(nameDisplay);
    }


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

    // Render other players' cards (face down)
    if (playerCount === 2) {
        const oppPlayer = players.find(p => p.player_num !== shownPlayer.player_num);
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
    
    // if the active player is the shown one, and the game is either online or there's only one human, show Your Turn
    if (isYourTurnNow) {
        text = `${player.color} Your Turn`;
        
        // Add visual highlight effect if it just became your turn
        if (!wasYourTurnBefore) {
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
    } else {
        // Parse the player representation correctly
        text = formatPlayerDisplay(player);
    }

    // Add styles to the turn info element based on whose turn it is
    turnInfo.textContent = text;
    
    if (isYourTurnNow) {
        turnInfo.style.fontWeight = 'bold';
        turnInfo.style.color = '#ff9500';
    } else {
        turnInfo.style.fontWeight = 'normal';
        turnInfo.style.color = '';
    }
    
    // If it's now your turn and wasn't before, add some CSS to make it noticeable
    if (!window.__addedTurnStyles) {
        window.__addedTurnStyles = true;
        const style = document.createElement('style');
        style.innerHTML = `
            .highlight-turn {
                animation: pulse 2s;
            }
            @keyframes pulse {
                0% { transform: scale(1); }
                25% { transform: scale(1.1); }
                50% { transform: scale(1); }
                75% { transform: scale(1.1); }
                100% { transform: scale(1); }
            }
        `;
        document.head.appendChild(style);
    }
}

// Helper function to handle player display formatting
function formatPlayerDisplay(player) {
    if (!player) return "";
    
    // If we have a stored username in localStorage, use that for the current player
    if (player.player_num === 1) { // Assuming player 1 is typically the current player
        const username = localStorage.getItem('username');
        if (username) {
            return `${player.color} ${username}`;
        }
    }
    
    // If repr property exists and looks correctly formatted, use it
    if (player.repr && !player.repr.includes('TeamName.')) {
        return player.repr;
    }
    
    // Otherwise construct a display name from available properties
    const playerType = player.is_person ? "Player" : "Computer";
    return `${player.color} ${playerType} ${player.player_num}`;
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

    const activePlayer = state.active_player;
    const playerNum = activePlayer.player_num;

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
