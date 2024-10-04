
    const volumeIcon = document.getElementById('volume-icon');
    const volumeSliderContainer = document.getElementById('volume-slider-container');

    // Показываем ползунок при наведении на иконку
    volumeIcon.addEventListener('mouseenter', function() {
        volumeSliderContainer.classList.add('show');
    });

    // Скрываем ползунок при уходе мыши с контейнера с ползунком
    volumeSliderContainer.addEventListener('mouseleave', function() {
        volumeSliderContainer.classList.remove('show');
    });


    function logout() {
        // Сделайте запрос на сервер для выхода
        window.location.href = "/auth/logout";
    }

    window.YaAuthSuggest.init(
    {
      client_id: "983a1fbebb3b4b6a851c645b7bb541bf",
      response_type: "token",
      redirect_uri: "http://localhost:8000/oauth.php?provider=yandex"
    },
    "http://localhost",
    { view: "default" }
  )
  .then(({handler}) => handler())
  .then(data => console.log('Сообщение с токеном', data))
  .catch(error => console.log('Обработка ошибки', error))

   YaSendSuggestToken('http://localhost:8000', {
      flag: true
   }
   )

    const audioPlayers = document.querySelectorAll('audio');
    const playButtons = document.querySelectorAll('.play-pause-btn');
    const globalVolumeSlider = document.getElementById('global-volume-slider');
    const popupModal = document.getElementById('popup-modal');
    const popupTrackImage = document.getElementById('popup-track-image');
    const popupTrackTitle = document.getElementById('popup-track-title');
    const popupTrackArtist = document.getElementById('popup-track-artist');
    const popupAudioPlayer = document.getElementById('popup-audio-player');
    const popupAudioSource = document.getElementById('popup-audio-source');
    const closePopup = document.getElementById('close-popup');
    const popupProgressBar = document.getElementById('popup-progress');
    const popupCurrentTime = document.getElementById('popup-current-time');
    const popupDurationTime = document.getElementById('popup-duration-time');
    const playPausePopup = document.getElementById('play-pause-popup');
    const prevTrack = document.getElementById('prev-track');
    const nextTrack = document.getElementById('next-track');

    let currentTrackIndex = 0;
    let isDragging = false;
    let isSeeking = false;
    let isModalOpen = false; // Переменная для отслеживания состояния модального окна

    globalVolumeSlider.addEventListener('input', () => {
        const volume = globalVolumeSlider.value;
        audioPlayers.forEach(player => {
            player.volume = volume;
        });
    });

    playButtons.forEach((playBtn, index) => {
        const audioPlayer = audioPlayers[index];

        playBtn.addEventListener('click', () => {
            console.log('Открытие модального окна'); // Лог
            updatePopupPlayer(index);
            popupModal.classList.remove('hidden');
            isModalOpen = true; // Устанавливаем состояние модального окна в открытое
        });

        audioPlayer.addEventListener('canplaythrough', () => {
            console.log(`Длительность трека ${index + 1}: ${audioPlayer.duration}`);
        });
    });

    function updatePopupPlayer(index) {
        const audioPlayer = audioPlayers[index];
        const trackImage = document.querySelector(`#image-${index + 1}`).src;
        const trackTitle = document.getElementById(`track-title-${index + 1}`).textContent;
        const trackArtist = document.getElementById(`track-artist-${index + 1}`).textContent;
        const trackFilePath = audioPlayer.querySelector('source').src;

        popupTrackImage.src = trackImage;
        popupTrackTitle.textContent = trackTitle;
        popupTrackArtist.textContent = trackArtist;
        popupAudioSource.src = trackFilePath;
        popupAudioPlayer.load();
        popupAudioPlayer.play();
        playPausePopup.querySelector('img').src = '/images/pause.png';

        popupAudioPlayer.addEventListener('loadedmetadata', () => {
            popupDurationTime.textContent = formatTime(popupAudioPlayer.duration);
        });

        popupAudioPlayer.addEventListener('timeupdate', () => {
            if (!isSeeking && isModalOpen) { // Проверка состояния модального окна
                const progressPercent = (popupAudioPlayer.currentTime / popupAudioPlayer.duration) * 100;
                popupProgressBar.style.width = progressPercent + '%';
                popupCurrentTime.textContent = formatTime(popupAudioPlayer.currentTime);

                // Проверка на окончание трека
                const currentPosition = popupAudioPlayer.currentTime;
                const duration = popupAudioPlayer.duration;

                // Если разница между текущей и предполагаемой позицией меньше 0.1, переключаем трек
                if (Math.abs(duration - currentPosition) < 0.1) {
                    currentTrackIndex = (currentTrackIndex + 1) % audioPlayers.length; // Увеличиваем индекс текущего трека
                    updatePopupPlayer(currentTrackIndex); // Обновляем плеер с новым треком
                }
            }
        });
    }

    function formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${minutes}:${secs < 10 ? '0' + secs : secs}`;
    }

    closePopup.addEventListener('click', () => {
        console.log('Закрытие модального окна'); // Лог
        popupAudioPlayer.pause();
        popupAudioPlayer.currentTime = 0; // Сбрасываем время воспроизведения
        popupModal.classList.add('hidden');
        isModalOpen = false; // Устанавливаем состояние модального окна в закрытое
    });

    prevTrack.addEventListener('click', () => {
        currentTrackIndex = (currentTrackIndex - 1 + audioPlayers.length) % audioPlayers.length;
        updatePopupPlayer(currentTrackIndex);
    });

    nextTrack.addEventListener('click', () => {
        currentTrackIndex = (currentTrackIndex + 1) % audioPlayers.length;
        updatePopupPlayer(currentTrackIndex);
    });

    playPausePopup.addEventListener('click', () => {
        if (popupAudioPlayer.paused) {
            popupAudioPlayer.play();
            playPausePopup.querySelector('img').src = '/images/pause.png';
        } else {
            popupAudioPlayer.pause();
            playPausePopup.querySelector('img').src = '/images/play.png';
        }
    });

    const popupProgressContainer = document.getElementById('popup-progress-container');

    popupProgressContainer.addEventListener('mousedown', (e) => {
        isDragging = true;
        isSeeking = true;
        seek(e);
    });

    document.addEventListener('mouseup', () => {
        isDragging = false;
        isSeeking = false;
    });

    document.addEventListener('mousemove', (e) => {
        if (isDragging) {
            seek(e);
        }
    });

    popupProgressContainer.addEventListener('click', (e) => {
        seek(e);
    });

    function seek(e) {
        const rect = popupProgressContainer.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const progressPercent = Math.max(0, Math.min(clickX / rect.width, 1));
        const newTime = progressPercent * popupAudioPlayer.duration;

        if (popupAudioPlayer.readyState > 0 && popupAudioPlayer.duration > 0) {
            popupAudioPlayer.currentTime = newTime;
            popupProgressBar.style.width = progressPercent * 100 + '%';

            console.log(`Новая позиция: ${newTime}, Текущая позиция: ${popupAudioPlayer.currentTime}`);

            if (!popupAudioPlayer.paused) {
                popupAudioPlayer.play();
            }
        } else {
            console.error("Трек не готов к воспроизведению или имеет некорректную длительность.");
            console.log("readyState:", popupAudioPlayer.readyState);
        }
    }

    popupAudioPlayer.addEventListener('error', (e) => {
        console.error('Произошла ошибка в плеере:', e);
        const error = e.target.error;
        if (error) {
            switch (error.code) {
                case error.MEDIA_ERR_ABORTED:
                    console.error('Воспроизведение было прервано пользователем.');
                    break;
                case error.MEDIA_ERR_NETWORK:
                    console.error('Проблема с сетевым соединением.');
                    break;
                case error.MEDIA_ERR_DECODE:
                    console.error('Ошибка при декодировании мультимедиа.');
                    break;
                case error.MEDIA_ERR_SRC_NOT_SUPPORTED:
                    console.error('Источник мультимедиа не поддерживается.');
                    break;
                default:
                    console.error('Неизвестная ошибка.');
                    break;
            }
        }
    });

        document.getElementById('uploadForm').addEventListener('submit', async function(event) {
            event.preventDefault();

            const formData = new FormData(this);
            const messageDiv = document.getElementById('message');

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    messageDiv.textContent = 'Файл успешно загружен!';
                    messageDiv.style.color = 'green';
                } else {
                    messageDiv.textContent = 'Ошибка при загрузке файла.';
                    messageDiv.style.color = 'red';
                }
            } catch (error) {
                messageDiv.textContent = 'Произошла ошибка: ' + error.message;
                messageDiv.style.color = 'red';
            }
        });

    async function addToMyMusic(event, trackId) {
    event.preventDefault(); // Останавливаем стандартное поведение формы

    const heartIcon = document.getElementById(`heart-${trackId}`);

    // Отправляем POST-запрос для добавления трека
    const formData = new FormData(event.target);
    const response = await fetch(event.target.action, {
        method: 'POST',
        body: formData,
    });

    console.log("Response status:", response.status); // Логируем статус ответа

    if (response.ok) {
        const result = await response.json();
        console.log("Result:", result); // Логируем результат

        // Убираем серый фильтр
        heartIcon.style.filter = "none";

        // Восстанавливаем серый фильтр через 1 секунду
        setTimeout(() => {
            heartIcon.style.filter = "grayscale(1)"; // Устанавливаем обратно серый фильтр
        }, 1000);
    } else {
        console.error('Ошибка при добавлении трека в плейлист.');
    }
}
