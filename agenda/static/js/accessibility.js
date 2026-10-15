document.addEventListener('DOMContentLoaded', () => {
    // Define o tamanho inicial da fonte (busca no localStorage ou assume 100%)
    let currentFontSize = parseInt(localStorage.getItem('fontSize')) || 100;
    const minFontSize = 80;   // Limite mínimo (80%)
    const maxFontSize = 140;  // Limite máximo (140%)
    const step = 10;          // Incremento por clique (10%)

    // Função para aplicar o tamanho da fonte na raiz do documento
    function applyFontSize(size) {
        document.documentElement.style.fontSize = `${size}%`;
        localStorage.setItem('fontSize', size);
    }

    // Aplica o tamanho guardado assim que a página carregar
    applyFontSize(currentFontSize);

    // Botão Aumentar (A+)
    const btnIncrease = document.getElementById('btn-increase-font');
    if (btnIncrease) {
        btnIncrease.addEventListener('click', () => {
            if (currentFontSize < maxFontSize) {
                currentFontSize += step;
                applyFontSize(currentFontSize);
            }
        });
    }

    // Botão Diminuir (A-)
    const btnDecrease = document.getElementById('btn-decrease-font');
    if (btnDecrease) {
        btnDecrease.addEventListener('click', () => {
            if (currentFontSize > minFontSize) {
                currentFontSize -= step;
                applyFontSize(currentFontSize);
            }
        });
    }

    // Botão Reset (A - Normal)
    const btnReset = document.getElementById('btn-reset-font');
    if (btnReset) {
        btnReset.addEventListener('click', () => {
            currentFontSize = 100;
            applyFontSize(currentFontSize);
        });
    }
});