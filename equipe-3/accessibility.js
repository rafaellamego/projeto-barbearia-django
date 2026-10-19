document.addEventListener('DOMContentLoaded', () => {
    const minFontSize = 80;
    const maxFontSize = 140;
    const step = 10;
    const status = document.getElementById('font-size-status');

    let savedSize = 100;
    try {
        const value = Number.parseInt(localStorage.getItem('fontSize'), 10);
        if (Number.isFinite(value) && value >= minFontSize && value <= maxFontSize) {
            savedSize = value;
        }
    } catch (_) {
        // O ajuste da fonte continua funcionando mesmo se o armazenamento estiver bloqueado.
    }
    let currentFontSize = savedSize;

    function applyFontSize(size) {
        currentFontSize = Math.min(maxFontSize, Math.max(minFontSize, size));
        document.documentElement.style.fontSize = `${currentFontSize}%`;
        try {
            localStorage.setItem('fontSize', String(currentFontSize));
        } catch (_) {
            // A preferência não persiste neste navegador, mas o tamanho atual foi aplicado.
        }
        if (status) status.textContent = `Tamanho do texto: ${currentFontSize} por cento.`;
    }

    applyFontSize(currentFontSize);

    document.getElementById('btn-increase-font')?.addEventListener('click', () => {
        applyFontSize(currentFontSize + step);
    });
    document.getElementById('btn-decrease-font')?.addEventListener('click', () => {
        applyFontSize(currentFontSize - step);
    });
    document.getElementById('btn-reset-font')?.addEventListener('click', () => {
        applyFontSize(100);
    });
});
