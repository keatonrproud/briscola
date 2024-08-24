
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


function playHumanCard(cardIndex, cardDiv) {
    cardDiv.classList.add('played'); // Add the class to trigger animation

    setTimeout(() => {
    fetch('/api/play_active_card', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ card_index: cardIndex }) // Send card index as JSON
    })
    .then(response => response.json())
    .then(async data =>  {
        // Handle the updated game state

        if (data.pile.cards.length === 0) {
            setTimeout(async () => {await updateGameState(data);}, 1500)
            } // Update the UI based on new game state
        else {updateGameState(data);}

        if (data.pile.cards.length === data.players.length) {
            setTimeout(() => {
                endPlay();
                }, 1500
            )
        } else {
            setTimeout(() => {endPlay();}, 500)
        }
    })
    .catch(error => console.error('Error:', error));
    }, 500)
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
async function playComputerCard(cardIndex, cardDiv) {

    // TODO add animation for computer card
    // cardDiv.classList.add('played'); // Add the class to trigger animation

    fetch('/api/play_active_card', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ card_index: cardIndex }) // Send card index as JSON
    })
    .then(response => response.json())
    .then(data => {
        updateGameState(data, continue_play=false); // Update the UI based on new game state
    })
    .catch(error => console.error('Error:', error));
}


function endPlay() {
    fetch('/api/end_play', {})
    .then(response => response.json())
    .then(data => {
        updateGameState(data);
    }) // Update the UI based on new game state
    .catch(error => console.error('Error:', error));

}

async function playComputerTurn(data) {
    // get their choice
    const computerChoice = await getComputerChoice();

    // play their card and update state
    const oppCardsContainer = document.getElementById('opp-cards');
    const oppCardDiv = Array.from(oppCardsContainer.children).indexOf(computerChoice);

    setTimeout(async () => {
        await playComputerCard(computerChoice, oppCardDiv);
        setTimeout(() => {
        endPlay();}, 1500)
    }, 1500)
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


// Call this function after fetching game data
function updateGameState(data, continue_play= true) {
    fetch('/api/get_state') // Adjust endpoint as necessary
        .then(response => response.json())
        .then(async data => {

            // Extract data for the active player
            const activePlayer = data.active_player;
            const playerNum = activePlayer.player_num; // Example: Player 1

            updateTurnInfo(activePlayer); // Update the turn info

            if (activePlayer.score - pastScores[playerNum] > 11) {
                const scoreboard = document.getElementById('scoreboard');
                const rect = scoreboard.getBoundingClientRect();
                const x = rect.left + rect.width / 2; // Horizontal center of the scoreboard
                const y = rect.top; // Top of the scoreboard

                showConfetti(xOrigin = x / window.innerWidth, yOrigin = y / window.innerHeight);
            }

            updateBriscolaCard(data.briscola.card, data.deck.current_cards.length); // Update the Briscola card
            updateScoreboard(data.players); // Update scoreboard
            updateDeck(data.deck.current_cards); // Update the deck


            let shownPlayer = data.shown_player;
            if (data.player && data.active_player.is_person) {
                shownPlayer = data.active_player;
            }

            updateActivePile(data.pile.cards, activePlayer, shownPlayer); // Update active pile


            const oppPlayer = data.players.find(other_player => other_player.player_num !== shownPlayer.player_num);
            const cardsPlayable = shownPlayer.player_num === data.active_player.player_num;

            updateCards(shownPlayer.hand.cards, oppPlayer.hand.cards, cardsPlayable);

            if (!data.active_player.is_person && continue_play) {
                await playComputerTurn(data);
            }

            if (!data.game_ongoing) {
                endGame();
            }

        })
        .catch(error => console.error('Error:', error));
}
