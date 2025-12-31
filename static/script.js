document.addEventListener('DOMContentLoaded', () => {
    const numberGrid = document.getElementById('numberGrid');
    const addGameBtn = document.getElementById('addGameBtn');
    const gamesList = document.getElementById('gamesList');
    const gameCountSpan = document.getElementById('gameCount');
    const submitBtn = document.getElementById('submitBtn');
    const errorMsg = document.getElementById('errorMsg');
    const fullNameInput = document.getElementById('fullName');

    let currentSelection = new Set();
    let games = [];
    const MAX_GAMES = 5;
    const NUMBERS_PER_GAME = 6;

    // Generate Grid
    for (let i = 1; i <= 60; i++) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'number-btn';
        btn.textContent = i;
        btn.onclick = () => toggleNumber(i, btn);
        numberGrid.appendChild(btn);
    }

    function toggleNumber(num, btn) {
        if (currentSelection.has(num)) {
            currentSelection.delete(num);
            btn.classList.remove('selected');
        } else {
            if (currentSelection.size >= NUMBERS_PER_GAME) {
                showError(`Máximo de ${NUMBERS_PER_GAME} números por jogo.`);
                return;
            }
            currentSelection.add(num);
            btn.classList.add('selected');
        }
        updateUI();
    }

    function updateUI() {
        errorMsg.textContent = '';
        addGameBtn.disabled = currentSelection.size !== NUMBERS_PER_GAME || games.length >= MAX_GAMES;

        // Also check if User Name is filled for final submit
        submitBtn.disabled = games.length === 0 || !fullNameInput.value.trim();
    }

    const randomBtn = document.getElementById('randomBtn');

    fullNameInput.addEventListener('input', updateUI);

    randomBtn.onclick = () => {
        resetSelection();
        const available = [];
        for (let i = 1; i <= 60; i++) available.push(i);

        // Shuffle
        for (let i = available.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [available[i], available[j]] = [available[j], available[i]];
        }

        // Select first 6
        const selection = available.slice(0, 6);
        selection.forEach(num => {
            currentSelection.add(num);
            const btn = numberGrid.children[num - 1];
            if (btn) btn.classList.add('selected');
        });

        updateUI();
    };

    addGameBtn.onclick = () => {

        if (currentSelection.size !== NUMBERS_PER_GAME) return;
        if (games.length >= MAX_GAMES) return;

        const numbers = Array.from(currentSelection).sort((a, b) => a - b);
        games.push(numbers);

        renderGames();
        resetSelection();
        updateUI();
    };

    function resetSelection() {
        currentSelection.clear();
        document.querySelectorAll('.number-btn').forEach(btn => btn.classList.remove('selected'));
    }

    function renderGames() {
        gamesList.innerHTML = '';
        games.forEach((game, index) => {
            const div = document.createElement('div');
            div.className = 'game-item';
            div.innerHTML = `
                <span class="game-numbers">Jogo ${index + 1}: [ ${game.join(', ')} ]</span>
                <button type="button" class="remove-game" onclick="removeGame(${index})">✕</button>
            `;
            gamesList.appendChild(div);
        });
        gameCountSpan.textContent = games.length;
    }

    // Specially expose removeGame to window scope
    window.removeGame = (index) => {
        games.splice(index, 1);
        renderGames();
        updateUI();
    };

    function showError(msg) {
        errorMsg.textContent = msg;
        setTimeout(() => { errorMsg.textContent = ''; }, 3000);
    }

    document.getElementById('gameForm').onsubmit = async (e) => {
        e.preventDefault();

        if (games.length === 0) return;
        if (!fullNameInput.value.trim()) {
            showError('Por favor, preencha seu nome.');
            return;
        }

        submitBtn.disabled = true;
        submitBtn.textContent = 'Enviando...';

        try {
            const response = await fetch('/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    fullName: fullNameInput.value,
                    games: games
                })
            });

            const result = await response.json();

            if (result.success) {
                window.location.href = result.redirect;
            } else {
                showError(result.message || 'Erro ao enviar jogos.');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Finalizar Apostas';
            }
        } catch (error) {
            console.error('Error:', error);
            showError('Erro de conexão.');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Finalizar Apostas';
        }
    };
});
