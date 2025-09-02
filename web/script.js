// --- ESTADO DA APLICAÇÃO ---
let currentPage = 1;
let totalPages = 1;
let currentActressName = '';
let currentSearchQuery = ''; // Armazena a query da busca atual
let currentSearchTag = null; // A tag principal da busca para o botão "próxima cena"
let isFetching = false; // Flag para evitar múltiplas requisições de scroll infinito

const sceneColors = ['#3498db', '#e74c3c', '#2ecc71', '#f1c40f', '#9b59b6', '#1abc9c', '#e67e22', '#f39c12'];
let videoDataCache = {};
let allAutocompleteTags = [];

// --- FUNÇÕES DE RENDERIZAÇÃO E LÓGICA PRINCIPAL ---

/**
 * Renderiza a galeria com uma nova lista de vídeos (usado para paginação ou a primeira busca).
 */
function renderGallery(response, isSearchResult = false) {
    const gallery = document.getElementById('video-gallery');
    const pagination = document.getElementById('pagination-controls');
    const clearButton = document.getElementById('clear-button');

    // Atualiza o estado da busca
    currentSearchQuery = isSearchResult ? response.search_query : '';
    currentSearchTag = isSearchResult ? response.highlight_tag : null;

    pagination.style.display = isSearchResult || response.videos.length === 0 ? 'none' : 'block';
    clearButton.style.display = isSearchResult ? 'inline-block' : 'none';

    if (response.error) { gallery.innerHTML = `<h2 style="color:red;">${response.error}</h2>`; return; }

    // Atualiza os controles de paginação (relevante apenas para a visualização normal)
    currentPage = response.currentPage;
    totalPages = response.totalPages;
    if (!isSearchResult) {
        updatePaginationControls();
    }

    gallery.innerHTML = ''; // Limpa a galeria para os novos resultados
    if (response.videos.length === 0) {
        gallery.innerHTML = isSearchResult ? `<h2>Nenhum vídeo encontrado para a busca "${response.search_query}".</h2>` : '<h2>Nenhum vídeo encontrado para esta atriz.</h2>';
        return;
    }

    appendResultsToGallery(response); // Usa a função de anexo para a renderização inicial
}

/**
 * Adiciona novos cards de vídeo ao final da galeria (usado pelo scroll infinito).
 */
function appendResultsToGallery(response) {
    const gallery = document.getElementById('video-gallery');

    // Atualiza o estado da paginação para o scroll infinito
    currentPage = response.currentPage;
    totalPages = response.totalPages;

    response.videos.forEach(video => {
        videoDataCache[video.video_id] = { scenes: null, activeTag: null };

        let tagsHtml = '<div class="tags-container">';
        if (video.main_tags) {
            video.main_tags.split('|||').forEach(tagWithScore => {
                const [tagName, score] = tagWithScore.split(':');
                tagsHtml += `<span class="tag" title="Confiança: ${score}" onclick="toggleTagFilter(${video.video_id}, '${tagName}')">${tagName}</span>`;
            });
        }
        tagsHtml += '</div>';

        const videoCard = document.createElement('div');
        videoCard.className = 'video-card';
        videoCard.innerHTML = `
            <video id="video-${video.video_id}" preload="metadata" controls loop muted></video>
            <div id="progress-container-${video.video_id}" class="custom-progress-bar-container">
                <div id="scene-bar-${video.video_id}" class="scene-progress-bar"></div>
                <div id="playhead-${video.video_id}" class="playhead"></div>
            </div>
            <div class="video-info">
                <div class="card-header">
                    <h3>${video.video_name}</h3>
                    <button class="next-scene-btn" onclick="jumpToNextScene(${video.video_id})">Próxima Cena &raquo;</button>
                </div>
                ${tagsHtml}
            </div>`;
        
        videoCard.querySelector('video').src = video.file_path;
        gallery.appendChild(videoCard);
        addEventListenersToVideo(video.video_id, response.highlight_tag);
    });
}


// --- LÓGICA DE BUSCA E NAVEGAÇÃO ---

async function performSearch(page = 1) {
    // Se for uma nova busca (página 1), limpa a galeria e define a query
    if (page === 1) {
        currentSearchQuery = document.getElementById('search-input').value;
        document.getElementById('video-gallery').innerHTML = `<h2>Buscando por "${currentSearchQuery}"...</h2>`;
    }

    if (!currentSearchQuery.trim() || isFetching) return;

    isFetching = true;
    
    const response = await eel.search_videos_by_tags(currentActressName, currentSearchQuery, page)();
    
    if (page === 1) {
        renderGallery(response, true);
    } else {
        appendResultsToGallery(response);
    }
    
    isFetching = false;
}

async function loadVideos(page) {
    const response = await eel.get_videos_page(currentActressName, page)();
    renderGallery(response, false);
}

// --- FUNÇÕES DO PLAYER E INTERATIVIDADE ---

function jumpToNextScene(videoId) {
    const videoElement = document.getElementById(`video-${videoId}`);
    const scenes = videoDataCache[videoId]?.scenes;
    if (!videoElement || !scenes || scenes.length === 0) return;
    
    const currentTime = videoElement.currentTime;
    let targetScenes = scenes;

    // Se uma busca estiver ativa, filtra as cenas para pular apenas entre as relevantes
    if (currentSearchTag) {
        targetScenes = scenes.filter(scene => scene.tags && scene.tags.split(',').includes(currentSearchTag));
        const btn = videoElement.closest('.video-card').querySelector('.next-scene-btn');
        if (btn) btn.innerHTML = `Próxima com "${currentSearchTag}" &raquo;`;
    }

    if (targetScenes.length === 0) return;

    let nextScene = targetScenes.find(scene => scene.start_time > currentTime + 0.1);

    if (!nextScene) {
        nextScene = targetScenes[0]; // Volta para o início se chegar ao fim
    }
    
    videoElement.currentTime = nextScene.start_time;
    videoElement.play();
}

function addEventListenersToVideo(videoId, highlightTag = null) {
    const videoElement = document.getElementById(`video-${videoId}`);
    const progressContainer = document.getElementById(`progress-container-${videoId}`);
    const playhead = document.getElementById(`playhead-${videoId}`);

    videoElement.addEventListener('loadedmetadata', async () => {
        const scenes = await eel.get_scenes_for_video(videoId)();
        videoDataCache[videoId].scenes = scenes;
        if (highlightTag) {
            setTimeout(() => toggleTagFilter(videoId, highlightTag), 100);
        } else {
            drawSceneBar(videoId, videoElement.duration);
        }
    });

    videoElement.addEventListener('timeupdate', () => {
        if (!videoElement.duration) return;
        const progressPercent = (videoElement.currentTime / videoElement.duration) * 100;
        playhead.style.left = `${progressPercent}%`;
    });

    progressContainer.addEventListener('click', (e) => {
        const rect = progressContainer.getBoundingClientRect();
        videoElement.currentTime = ((e.clientX - rect.left) / progressContainer.offsetWidth) * videoElement.duration;
    });
}

function toggleTagFilter(videoId, clickedTag) {
    const videoData = videoDataCache[videoId];
    const videoElement = document.getElementById(`video-${videoId}`);
    videoData.activeTag = (videoData.activeTag === clickedTag) ? null : clickedTag;
    const card = videoElement.closest('.video-card');
    card.querySelectorAll('.tag').forEach(tagEl => {
        tagEl.classList.toggle('active', tagEl.innerText === videoData.activeTag);
    });
    drawSceneBar(videoId, videoElement.duration, videoData.activeTag);
}

function drawSceneBar(videoId, totalDuration, filterTag = null) {
    const sceneBar = document.getElementById(`scene-bar-${videoId}`);
    const scenes = videoDataCache[videoId].scenes;
    if (!scenes) return;
    sceneBar.innerHTML = '';
    scenes.forEach((scene, index) => {
        const segment = document.createElement('div');
        segment.className = 'scene-segment';
        const segmentDuration = scene.end_time - scene.start_time;
        const segmentWidth = (segmentDuration / totalDuration) * 100;
        if (filterTag && (!scene.tags || !scene.tags.split(',').includes(filterTag))) {
            segment.classList.add('faded');
        }
        segment.style.width = `${segmentWidth}%`;
        segment.style.backgroundColor = sceneColors[index % sceneColors.length];
        segment.title = `Cena ${index + 1}: ${scene.start_time.toFixed(1)}s - ${scene.end_time.toFixed(1)}s [${scene.tags || ''}]`;
        sceneBar.appendChild(segment);
    });
}

function updatePaginationControls() {
    document.getElementById('page-info').textContent = `Página ${currentPage} de ${totalPages}`;
    document.getElementById('prev-button').disabled = (currentPage <= 1);
    document.getElementById('next-button').disabled = (currentPage >= totalPages);
}

function setupAutocomplete(input, tags) {
    // ... (código do autocomplete sem alterações)
    let currentFocus;input.addEventListener("input",function(e){let a,b,i,val=this.value;closeAllLists();if(!val)return false;currentFocus=-1;a=document.createElement("DIV");a.setAttribute("id",this.id+"autocomplete-list");a.setAttribute("class","autocomplete-items");this.parentNode.appendChild(a);const lastTokenIndex=val.lastIndexOf(' ')+1;const lastToken=val.substring(lastTokenIndex).toLowerCase();if(!lastToken)return;for(i=0;i<tags.length;i++){if(tags[i].substr(0,lastToken.length).toLowerCase()==lastToken){b=document.createElement("DIV");b.innerHTML="<strong>"+tags[i].substr(0,lastToken.length)+"</strong>";b.innerHTML+=tags[i].substr(lastToken.length);b.addEventListener("click",function(e){const base=val.substring(0,lastTokenIndex);const tagToAdd=tags[i].includes(' ')?`"${tags[i]}"`:tags[i];input.value=base+tagToAdd+' ';closeAllLists();input.focus();});a.appendChild(b);}}});function closeAllLists(elmnt){var x=document.getElementsByClassName("autocomplete-items");for(var i=0;i<x.length;i++){if(elmnt!=x[i]&&elmnt!=input){x[i].parentNode.removeChild(x[i]);}}}document.addEventListener("click",function(e){closeAllLists(e.target);});
}

// --- INICIALIZAÇÃO E EVENTOS GLOBAIS ---
document.addEventListener('DOMContentLoaded', async () => {
    const params = new URLSearchParams(window.location.search);
    currentActressName = decodeURIComponent(params.get('actress'));
    if (!currentActressName || currentActressName === 'null') {
        document.body.innerHTML = '<h1>ERRO: Nenhuma atriz especificada.</h1>'; return;
    }
    document.querySelector('h1').innerText = `Galeria de Cenas: ${currentActressName}`;
    document.title = `Galeria: ${currentActressName}`;

    const tagsJson = await eel.get_all_tags_for_autocomplete()();
    allAutocompleteTags = JSON.parse(tagsJson);
    setupAutocomplete(document.getElementById("search-input"), allAutocompleteTags);

    document.getElementById('search-button').addEventListener('click', () => performSearch(1));
    document.getElementById('search-input').addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); performSearch(1); } });
    document.getElementById('clear-button').addEventListener('click', () => {
        document.getElementById('search-input').value = '';
        currentSearchQuery = '';
        loadVideos(1);
    });

    document.getElementById('prev-button').addEventListener('click', () => { if (currentPage > 1) loadVideos(currentPage - 1); });
    document.getElementById('next-button').addEventListener('click', () => { if (currentPage < totalPages) loadVideos(currentPage + 1); });

    loadVideos(1);
});

// Evento de scroll para a busca infinita
window.onscroll = () => {
    if (!currentSearchQuery || isFetching || currentPage >= totalPages) return;
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 500) {
        performSearch(currentPage + 1);
    }
};