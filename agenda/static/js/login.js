document.addEventListener('DOMContentLoaded', () => {
    const inputTelefone = document.getElementById('telefone');

    if (inputTelefone) {
        inputTelefone.addEventListener('input', (e) => {
            let valor = e.target.value.replace(/\D/g, "");
            
            if (valor.length > 11) {
                valor = valor.substring(0, 11);
            }

            let valorFormatado = "";

            if (valor.length > 10) {
                valorFormatado = `(${valor.substring(0, 2)}) ${valor.substring(2, 7)}-${valor.substring(7, 11)}`;
            } else if (valor.length > 6) {
                valorFormatado = `(${valor.substring(0, 2)}) ${valor.substring(2, 6)}-${valor.substring(6, 10)}`;
            } else if (valor.length > 2) {
                valorFormatado = `(${valor.substring(0, 2)}) ${valor.substring(2)}`;
            } else if (valor.length > 0) {
                valorFormatado = `(${valor}`;
            }

            e.target.value = valorFormatado;
        });
    }
});