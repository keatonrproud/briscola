

function updateCards(cards) {
    const cardsContainer = document.getElementById('player-cards');
    cardsContainer.innerHTML = '';  // Clear existing cards

    cards.forEach((card) => {
        const cardDiv = document.createElement('div');

        // Add click event listener to each card
        cardDiv.addEventListener('click', () => {
            const cardIndex = Array.from(cardsContainer.children).indexOf(cardDiv);
            playCard(cardIndex, cardDiv); // Pass the position of the current card
        });

        cardDiv.className = 'card';
        cardDiv.innerHTML = `
            <div class="symbol">${card.suit.symbol}</div>
            <div class="number">${card.number.name}</div>
        `;

        cardsContainer.appendChild(cardDiv);
    });
}

function updateTurnInfo(playerNum, color) {
    const turnInfo = document.getElementById('turn-info');
    turnInfo.textContent = `${color} Player ${playerNum}'s Turn`;
}

function updateBriscolaCard(card, num_cards_in_deck) {
    const briscolaCard = document.getElementById('briscola-card');

    if (card) {
        briscolaCard.querySelector('.symbol').textContent = card.suit.symbol;
        if (num_cards_in_deck > 0) {
            briscolaCard.querySelector('.number').textContent = card.number.name;
        } else {
            briscolaCard.querySelector('.number').textContent = '';
        }
    } else {
        briscolaCard.querySelector('.symbol').textContent = '';
        briscolaCard.querySelector('.number').textContent = '';
    }
}


function playCard(cardIndex, cardDiv) {
    cardDiv.classList.add('played'); // Add the class to trigger animation

    setTimeout(() => {
    fetch('/api/play_card', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ card_index: cardIndex }) // Send card index as JSON
    })
    .then(response => response.json())
    .then(data => {
        // Handle the updated game state
        updateGameState(data); // Update the UI based on new game state
    })
    .catch(error => console.error('Error:', error));
    }, 500)
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

// Example usage: Draw a card when the deck is clicked
document.querySelector('.deck-container').addEventListener('click', drawCard);

function updateActivePile(cards) {
    const activePileContainer = document.getElementById('active-pile');
    activePileContainer.innerHTML = '';  // Clear existing cards

    if (cards.length === 0) {
        activePileContainer.style.backgroundColor = 'transparent'; // Hide background if empty
        activePileContainer.style.border = 'none'; // Remove border if empty
    } else {
        activePileContainer.style.backgroundColor = '#f1f1f1'; // Default background color
        activePileContainer.style.border = '1px solid #ccc'; // Default border
    }

    cards.forEach(card => {
        const cardDiv = document.createElement('div');
        cardDiv.className = 'card';
        cardDiv.innerHTML = `
            <div class="symbol">${card.suit.symbol}</div>
            <div class="number">${card.number.name}</div>
        `;

        activePileContainer.appendChild(cardDiv);
    });
}

function endGame() {
    window.location.href = '/end_game';
}

// Call this function after fetching game data
function updateGameState() {
    fetch('/api/get_state') // Adjust endpoint as necessary
        .then(response => response.json())
        .then(data => {

            console.log(data);

            // Extract data for the active player
            const player = data.active_player;
            const playerNum = player.player_num; // Example: Player 1
            const color = player.color; // Example: 🟦
            updateTurnInfo(playerNum, color); // Update the turn info

            if (player.score - pastScores[playerNum] > 11) {
                const scoreboard = document.getElementById('scoreboard');
                const rect = scoreboard.getBoundingClientRect();
                const x = rect.left + rect.width / 2; // Horizontal center of the scoreboard
                const y = rect.top; // Top of the scoreboard

                showConfetti(xOrigin=x/window.innerWidth, yOrigin=y/window.innerHeight);
            }

            updateBriscolaCard(data.briscola.card, data.deck.current_cards.length); // Update the Briscola card
            updateCards(player.hand.cards); // Pass cards to updateCards
            updateScoreboard(data.players); // Update scoreboard
            updateDeck(data.deck.current_cards); // Update the deck
            updateActivePile(data.pile.cards); // Update active player

            if (!data.game_ongoing) {
                endGame();
            }

        })
        .catch(error => console.error('Error:', error));
}
