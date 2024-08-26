import { socket } from '/static/js/websocket.js'; // Import socket instance
export { updateGameState };

function setCardImage(cardDiv, card) {
    if (card && card.number && card.suit) {
        cardDiv.style.backgroundImage = `url('/static/piacentine/${card.number.name}_${card.suit.name}.png')`;
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

        // Add click event listener to each card
        if (cardsPlayable) {
            cardDiv.addEventListener('click', () => {
                const cardIndex = Array.from(playerCardsContainer.children).indexOf(cardDiv);
                playHumanCard(cardIndex, cardDiv); // Pass the position of the current card
            });
        }

        cardDiv.className = 'card';
        playerCardsContainer.appendChild(cardDiv);

        setCardImage(cardDiv, card);
    });

    const oppCardsContainer = document.getElementById('opp-cards');
    oppCardsContainer.innerHTML = '';  // Clear existing cards

    oppCards.forEach((_) => {
        const oppCardDiv = document.createElement('div');

        oppCardDiv.className = 'card';
        oppCardsContainer.appendChild(oppCardDiv);
    });
}

function updateTurnInfo(player) {
    const turnInfo = document.getElementById('turn-info');

    if (player.is_person) {
        turnInfo.textContent = `${player.color} Player ${player.player_num}'s Turn`;
    } else {
        turnInfo.textContent = `${player.color} Computer's Turn`;
    }
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

function setUpHumanCardPlayedListener() {
    if (!socket.__humanCardPlayedSetUp) {

        // Listen for the response from the server
        socket.on('active_card_played', async (data) => {
            if (!data.active_player.is_person) {
                return;
            }
            // Handle the updated game state
            if (data.pile.cards.length === 0) {
                setTimeout(async () => { await getGameState(); }, 1500);
            } else {
                await getGameState();
            }

            if (data.pile.cards.length === data.players.length) {
                setTimeout(() => {
                    console.log("END1");
                    endPlay();
                }, 1500);
            } else {
                setTimeout(() => {
                    console.log("END2");
                    endPlay(); }, 500);
            }
        });


        socket.__humanCardPlayedSetUp = true;
    }

}

async function playHumanCard(cardIndex, cardDiv) {
    cardDiv.classList.add('played'); // Add the class to trigger animation

    console.log('playing human card');

    setTimeout(() => {
        // Emit event to the server with the card index
        setUpHumanCardPlayedListener();
        socket.emit('play_active_card', { card_index: cardIndex });

    }, 500);
}


async function getComputerChoice() {
    console.log('getting computer choice');
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
                console.log('getting play computer card state')
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
    for (let i = 0; i < cardNum-1; i++) {
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


async function updateGameState(data) {
    // Extract data for the active player
    const state = data.game_state;

    console.log(state);

    const activePlayer = state.active_player;
    const playerNum = activePlayer.player_num; // Example: Player 1

    updateTurnInfo(activePlayer); // Update the turn info

    if (activePlayer.score - pastScores[playerNum] > 11) {
        const scoreboard = document.getElementById('scoreboard');
        const rect = scoreboard.getBoundingClientRect();
        const x = rect.left + rect.width / 2; // Horizontal center of the scoreboard
        const y = rect.top; // Top of the scoreboard

        showConfetti(x / window.innerWidth,  y / window.innerHeight);
    }

    updateBriscolaCard(state.briscola.card, state.deck.current_cards.length); // Update the Briscola card
    updateScoreboard(state.players); // Update scoreboard
    updateDeck(state.deck.current_cards); // Update the deck


    let shownPlayer = state.shown_player;
    // is shown player is not fixed, and the active player is a person
    if (!state.fixed_shown_player && state.table_settings.computer_count === 0 && activePlayer.is_person) {
        shownPlayer = activePlayer;
    }

    updateActivePile(state.pile.cards, activePlayer, shownPlayer); // Update active pile

    const oppPlayer = state.players.find(other_player => other_player.player_num !== shownPlayer.player_num);
    const cardsPlayable = shownPlayer.player_num === activePlayer.player_num;

    updateCards(shownPlayer.hand.cards, oppPlayer.hand.cards, cardsPlayable);

    console.log('==========');
    console.log(state);
    const activePlayerIsFirst = state.turn_order[0].player_num === activePlayer.player_num;
    const noComputerCardPlayed = (state.pile.cards.length === 0 && activePlayerIsFirst) || (activePlayer.hand.cards.length === 3 && state.pile.cards.length < state.players.length);
    if (!activePlayer.is_person && noComputerCardPlayed){
        console.log('Playing Computer turn');
        await playComputerTurn(state.turn_order[state.turn_order.length-1].player_num === activePlayer.player_num);
    }

    if (!state.game_ongoing) {
        endGame();
    }




}
