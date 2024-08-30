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

function updateCards(playerCards, oppCards, cardsPlayable) {
    const playerCardsContainer = document.getElementById('player-cards');
    playerCardsContainer.innerHTML = '';  // Clear existing cards

    playerCards.forEach((card) => {
        const cardDiv = document.createElement('div');

        setCardImage(cardDiv, card);

        // Named function for the event listener
        function handleCardClick(event) {
            const cardIndex = Array.from(playerCardsContainer.children).indexOf(cardDiv);
            playHumanCard(cardIndex, cardDiv); // Pass the position of the current card
        }

        // Add click event listener to each card IF they are allowed to be played
        if (cardsPlayable) {
            cardDiv.addEventListener('click', handleCardClick);

            // Store reference to the event handler function for potential removal
            cardDiv.handleCardClick = handleCardClick;
        }


        cardDiv.className = 'card';
        playerCardsContainer.appendChild(cardDiv);
    });

    const oppCardsContainer = document.getElementById('opp-cards');
    oppCardsContainer.innerHTML = '';  // Clear existing cards

    oppCards.forEach((_) => {
        const oppCardDiv = document.createElement('div');

        oppCardDiv.className = 'card';
        oppCardsContainer.appendChild(oppCardDiv);
    });
}

function updateTurnInfo(player, shownPlayer) {
    const turnInfo = document.getElementById('turn-info');

    let text = ""
    if (player.player_num === shownPlayer.player_num) {
        text = `${player.color} Your Turn`
    }
    else if (player.is_person) {
        text = `${player.color} Player ${player.player_num}'s Turn`;
    } else {
        text = `${player.color} Computer's Turn`;
    }

    turnInfo.textContent = text
}

function updateBriscolaCard(card, num_cards_in_deck) {
    const briscolaCard = document.getElementById('briscola-card');

    if (briscolaCard) {
        if (card) {
            if (num_cards_in_deck > 0) {
                setCardImage(briscolaCard, card);
            } else {
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

function checkIfInGame() {
    setUpInGameResultListener();
    socket.emit("check_if_in_game");
}

function setUpHumanCardPlayedListener() {
    if (!socket.__humanCardPlayedSetUp) {

        // Listen for the response from the server
        socket.on('active_card_played', async (data) => {
            if (!data.active_player.is_person) {
                return;
            }
            // Handle the updated game state
            if (data.pile.cards.length === 0) {
                setTimeout(async () => { await getGameState(); }, 500);
            } else {
                await getGameState();
            }

            if (data.pile.cards.length === data.players.length) {
                setTimeout(() => {
                    endPlay();
                }, 1500);
            } else {endPlay();}
        });


        socket.__humanCardPlayedSetUp = true;
    }

}

async function playHumanCard(cardIndex, cardDiv) {

    // set all other cards to be unplayable
    const playerCardsContainer = document.getElementById('player-cards');
    Array.from(playerCardsContainer.children).forEach(cardDiv => {
        cardDiv.removeEventListener('click', cardDiv.handleCardClick);
        delete cardDiv.handleCardClick;
    })


    cardDiv.classList.add('played'); // Add the class to trigger animation

    setTimeout(() => {
        // Emit event to the server with the card index
        setUpHumanCardPlayedListener();
        socket.emit('play_active_card', { card_index: cardIndex });

    }, 500);
}


async function getComputerChoice() {
    try {
        const response = await fetch('/api/get_computer_choice');
        const data = await response.json();
        return data.card_idx;
    } catch (error) {
        console.error('Error:', error);
    }
}

function setUpComputerCardPlayedListener() {
    if (!socket.__computerCardPlayedSetUp) {
        socket.on('active_card_played', (data) => {
            if (!data.active_player.is_person) {
                getGameState();
            }
        });

        socket.__computerCardPlayedSetUp = true;
    }

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
function updateScoreboard(players) {
    const scoresContainer = document.getElementById('scores');
    scoresContainer.innerHTML = ''; // Clear existing scores

    players.forEach(player => {
        const scoreDiv = document.createElement('div');
        scoreDiv.className = 'score';
        scoreDiv.innerHTML = `
            <span>Player ${player.player_num}:</span>
            <span>${player.score}</span>
        `;
        scoresContainer.appendChild(scoreDiv);

        pastScores[player.player_num]  = player.score;
    });
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

    const activePlayer = state.active_player;
    const playerNum = activePlayer.player_num; // Example: Player 1

    if (activePlayer.score - pastScores[playerNum] > 11) {
        blastConfettiForBigScore()
    }

    updateBriscolaCard(state.briscola.card, state.deck.current_cards.length); // Update the Briscola card
    updateScoreboard(state.players); // Update scoreboard
    updateDeck(state.deck.current_cards); // Update the deck


    let shownPlayer = state.shown_player;
    // is shown player is not fixed, and the active player is a person
    if (!state.fixed_shown_player && state.table_settings.computer_count === 0 && activePlayer.is_person) {
        shownPlayer = activePlayer;
    } else if (state.fixed_shown_player) {
        try {
            const response = await fetch('/api/convert_socketid_to_oid', {method: 'POST', headers: {
            'Content-Type': 'application/json'},body: JSON.stringify({ socket_id: socket.id })})
            const res = await response.json();
            shownPlayer = state.players[state.userid_playernum_map[res.oid]];
        } catch (error) {
            console.error('Error:', error);
        }
    }

    const oppPlayer = state.players.find(other_player => other_player.player_num !== shownPlayer.player_num);
    const cardsPlayable = shownPlayer.player_num === activePlayer.player_num;

    updateCards(shownPlayer.hand.cards, oppPlayer.hand.cards, cardsPlayable);

    updateTurnInfo(activePlayer, shownPlayer); // Update the turn info
    updateActivePile(state.pile.cards, activePlayer, shownPlayer); // Update active pile


    const activePlayerIsFirst = state.turn_order[0].player_num === activePlayer.player_num;
    const noComputerCardPlayed = (state.pile.cards.length === 0 && activePlayerIsFirst) || (activePlayer.hand.cards.length === 3 && state.pile.cards.length < state.players.length);
    if (!activePlayer.is_person && noComputerCardPlayed){
        await playComputerTurn(state.turn_order[state.turn_order.length-1].player_num === activePlayer.player_num);
    }

    if (!state.game_ongoing) {
        endGame();
    }
}

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
