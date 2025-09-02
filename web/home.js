/**
 * Manipula a lógica da tela inicial (home.html).
 */
document.addEventListener('DOMContentLoaded', async () => {
    const buttonsContainer = document.getElementById('actress-buttons');
    const mainArt = document.getElementById('main-art');
    const mainArtVideo = document.getElementById('main-art-video');
    
    // Mostra um feedback de carregamento
    buttonsContainer.innerHTML = '<p class="loading-text">Carregando atrizes...</p>';

    // Busca a lista de atrizes no backend Python
    const actresses = await eel.get_all_actresses()();
    
    // Limpa a mensagem de carregamento
    buttonsContainer.innerHTML = '';

    if (actresses && actresses.length > 0) {
        // Define a arte principal com o vídeo da primeira atriz da lista
        // (usando um vídeo como fundo é mais dinâmico que uma imagem)
        mainArtVideo.src = actresses[0].file_path;
        mainArtVideo.play();

        // Cria um botão para cada atriz
        actresses.forEach(actress => {
            const button = document.createElement('button');
            button.className = 'actress-btn';
            button.innerText = actress.actress;

            // Define a ação de clique para navegar para a galeria
            button.onclick = () => viewActressGallery(actress.actress);
            
            // Bônus: muda o vídeo de fundo ao passar o mouse sobre o botão
            button.onmouseover = () => {
                if (mainArtVideo.src !== actress.file_path) {
                    mainArtVideo.src = actress.file_path;
                    mainArtVideo.play();
                }
            };
            buttonsContainer.appendChild(button);
        });
    } else {
        buttonsContainer.innerHTML = '<p class="loading-text">Nenhuma atriz encontrada no banco de dados.</p>';
    }
});

/**
 * Navega para a página da galeria, usando um caminho absoluto a partir da raiz do servidor.
 * @param {string} actressName - O nome da atriz selecionada */
function viewActressGallery(actressName) {
    const encodedName = encodeURIComponent(actressName);
    
    // [CONFIGURAÇÃO FINAL E CORRETA]
    // Como a raiz do servidor é a pasta 'web', o caminho para a galeria é simplesmente 'gallery.html'
    window.location.href = `gallery.html?actress=${encodedName}`;
}