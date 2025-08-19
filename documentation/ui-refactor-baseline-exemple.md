```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lecteur Musical v2</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            color: #333;
        }

        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }

        /* Header */
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            background: white;
            padding: 15px 25px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .logo img {
            width: 40px;
            height: 40px;
            border-radius: 8px;
        }

        .nav {
            display: flex;
            gap: 25px;
        }

        .nav-item {
            padding: 8px 16px;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.2s ease;
            font-weight: 500;
        }

        .nav-item.active {
            background: #ff6b6b;
            color: white;
        }

        .nav-item:hover:not(.active) {
            background: #f0f0f0;
        }

        .social-icons {
            display: flex;
            gap: 10px;
        }

        .social-icon {
            width: 35px;
            height: 35px;
            border-radius: 50%;
            background: #f8f9fa;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 14px;
        }

        .social-icon:hover {
            background: #e9ecef;
            transform: translateY(-2px);
        }

        /* Player Section */
        .player-section {
            background: white;
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            text-align: center;
        }

        .track-title {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 8px;
            color: #2d3748;
        }

        .track-duration {
            color: #718096;
            font-size: 14px;
            margin-bottom: 30px;
        }

        /* Progress Bar */
        .progress-container {
            margin: 25px 0;
        }

        .progress-bar {
            width: 100%;
            height: 4px;
            background: #e2e8f0;
            border-radius: 2px;
            overflow: hidden;
            cursor: pointer;
        }

        .progress-fill {
            height: 100%;
            background: #ff6b6b;
            border-radius: 2px;
            width: 0%;
            transition: width 0.1s ease;
        }

        .time-indicators {
            display: flex;
            justify-content: space-between;
            margin-top: 8px;
            font-size: 12px;
            color: #718096;
        }

        /* Controls */
        .controls {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 15px;
            margin-top: 25px;
        }

        .control-btn {
            width: 45px;
            height: 45px;
            border-radius: 50%;
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            color: #4a5568;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
            font-size: 16px;
        }

        .play-btn {
            width: 60px;
            height: 60px;
            background: #ff6b6b;
            color: white;
            border: none;
            font-size: 20px;
        }

        .control-btn:hover {
            background: #edf2f7;
            transform: translateY(-2px);
        }

        .play-btn:hover {
            background: #e53e3e;
        }

        /* Playlists */
        .playlists-section {
            background: white;
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }

        .playlists-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .playlists-title {
            font-size: 20px;
            font-weight: 600;
            color: #2d3748;
        }

        .modify-btn {
            background: #ff6b6b;
            border: none;
            padding: 8px 16px;
            border-radius: 15px;
            color: white;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .modify-btn:hover {
            background: #e53e3e;
            transform: translateY(-2px);
        }

        .modify-btn.active {
            background: #38a169;
        }

        /* Playlist Items */
        .playlist-item {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 12px;
            transition: all 0.2s ease;
            border: 1px solid #e9ecef;
            cursor: pointer;
        }

        .playlist-item:hover {
            background: #f1f3f4;
            transform: translateX(5px);
        }

        .playlist-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .playlist-info h3 {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 4px;
            color: #2d3748;
        }

        .playlist-meta {
            color: #718096;
            font-size: 13px;
        }

        .playlist-actions {
            display: flex;
            gap: 10px;
            align-items: center;
        }

        .playlist-play-btn {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #ff6b6b;
            border: none;
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
            font-size: 14px;
        }

        .playlist-play-btn:hover {
            background: #e53e3e;
            transform: scale(1.05);
        }

        .nfc-btn {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #4299e1;
            border: none;
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
            font-size: 16px;
        }

        .nfc-btn:hover {
            background: #3182ce;
            transform: scale(1.05);
        }

        /* Upload Zone in Edit Mode */
        .playlist-upload-zone {
            margin-top: 15px;
            border: 2px dashed #cbd5e0;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            background: #f8f9fa;
            display: none;
        }

        .playlist-upload-zone.show {
            display: block;
        }

        .playlist-upload-zone:hover {
            border-color: #ff6b6b;
            background: #fff5f5;
        }

        .upload-text-small {
            font-size: 14px;
            color: #4a5568;
            margin-bottom: 5px;
        }

        .upload-subtext-small {
            font-size: 12px;
            color: #718096;
        }

        /* Playlist Content */
        .playlist-content {
            display: none;
            margin-top: 15px;
            border-top: 1px solid #e2e8f0;
            padding-top: 15px;
        }

        .playlist-content.show {
            display: block;
        }

        .track-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 12px;
            border-radius: 8px;
            margin-bottom: 5px;
            transition: all 0.2s ease;
        }

        .track-item:hover {
            background: rgba(255, 107, 107, 0.1);
        }

        .track-number {
            color: #4ecdc4;
            font-weight: 500;
            width: 25px;
        }

        .track-name {
            flex: 1;
            margin-left: 15px;
            font-size: 14px;
            color: #2d3748;
        }

        .track-duration {
            color: #718096;
            font-size: 12px;
        }

        /* NFC Modal */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.6);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            backdrop-filter: blur(5px);
        }

        .modal-overlay.active {
            display: flex;
        }

        .nfc-modal {
            background: white;
            border-radius: 20px;
            width: 90%;
            max-width: 400px;
            padding: 30px;
            text-align: center;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            animation: modalSlideIn 0.3s ease;
        }

        @keyframes modalSlideIn {
            from {
                transform: translateY(-50px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }

        .modal-close {
            position: absolute;
            top: 15px;
            right: 15px;
            width: 30px;
            height: 30px;
            border: none;
            background: #f8f9fa;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            color: #4a5568;
            transition: all 0.2s ease;
        }

        .modal-close:hover {
            background: #e9ecef;
        }

        .nfc-icon {
            font-size: 60px;
            color: #4299e1;
            margin-bottom: 20px;
        }

        .nfc-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 10px;
            color: #2d3748;
        }

        .nfc-subtitle {
            color: #718096;
            margin-bottom: 20px;
        }

        .nfc-status {
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            font-size: 14px;
        }

        .nfc-waiting {
            background: #fff5f5;
            color: #c53030;
            border: 1px solid #fed7d7;
        }

        .nfc-success {
            background: #f0fff4;
            color: #22543d;
            border: 1px solid #c6f6d5;
        }

        .cancel-btn {
            background: #e2e8f0;
            border: none;
            padding: 10px 20px;
            border-radius: 10px;
            color: #4a5568;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.2s ease;
        }

        .cancel-btn:hover {
            background: #cbd5e0;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .header {
                flex-direction: column;
                gap: 15px;
            }

            .playlist-item {
                text-align: center;
            }

            .playlist-header {
                flex-direction: column;
                gap: 15px;
            }

            .playlist-actions {
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <div class="logo">
                <img src="data:image/svg+xml,%3Csvg viewBox='0 0 40 40' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='40' height='40' rx='8' fill='%23ff6b6b'/%3E%3Cpath d='M15 12v16l12-8-12-8z' fill='white'/%3E%3C/svg%3E" alt="Logo">
            </div>

            <nav class="nav">
                <div class="nav-item active">Accueil</div>
                <div class="nav-item">À propos</div>
                <div class="nav-item">Réglages</div>
            </nav>

            <div class="social-icons">
                <div class="social-icon">💿</div>
                <div class="social-icon">🎧</div>
                <div class="social-icon">🔗</div>
                <div class="social-icon">❤️</div>
            </div>
        </header>

        <!-- Player Section -->
        <section class="player-section">
            <h1 class="track-title">Aucun morceau sélectionné</h1>
            <p class="track-duration">Durée: 00:00</p>

            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <div class="time-indicators">
                    <span>0:00</span>
                    <span>0:00</span>
                </div>
            </div>

            <div class="controls">
                <button class="control-btn">⏮</button>
                <button class="control-btn">⏪</button>
                <button class="control-btn play-btn">▶</button>
                <button class="control-btn">⏩</button>
                <button class="control-btn">⏭</button>
            </div>
        </section>

        <!-- Playlists Section -->
        <section class="playlists-section">
            <div class="playlists-header">
                <h2 class="playlists-title">Playlists</h2>
                <button class="modify-btn" id="modifyBtn" onclick="toggleEditMode()">Modifier</button>
            </div>

            <!-- Playlist 1 -->
            <div class="playlist-item" onclick="togglePlaylist('playlist1')">
                <div class="playlist-header">
                    <div class="playlist-info">
                        <h3>Zelda & Sleep</h3>
                        <p class="playlist-meta">30 tracks • Total Duration: 1h28m • Last Played: Never</p>
                    </div>
                    <div class="playlist-actions">
                        <button class="playlist-play-btn" title="Lire la playlist" onclick="event.stopPropagation()">▶</button>
                        <button class="nfc-btn" title="Associer tag NFC" onclick="event.stopPropagation(); openNfcModal('Zelda & Sleep')">📱</button>
                    </div>
                </div>

                <div class="playlist-upload-zone" onclick="event.stopPropagation(); document.getElementById('fileInput1').click()">
                    <div class="upload-text-small">📁 Ajouter des fichiers</div>
                    <div class="upload-subtext-small">MP3, WAV, FLAC, M4A</div>
                    <input type="file" id="fileInput1" style="display: none;" multiple accept=".mp3,.wav,.flac,.m4a">
                </div>

                <div class="playlist-content" id="playlist1-content">
                    <div class="track-item">
                        <span class="track-number">1</span>
                        <span class="track-name">A la volette [zV-Rl7VVagw]</span>
                        <span class="track-duration">01:59</span>
                    </div>
                    <div class="track-item">
                        <span class="track-number">2</span>
                        <span class="track-name">Alouette, gentille alouette [l4agyil_12s]</span>
                        <span class="track-duration">02:13</span>
                    </div>
                    <div class="track-item">
                        <span class="track-number">3</span>
                        <span class="track-name">Au clair de la lune, trois petits lapins [NwnkXUJ9MPs]</span>
                        <span class="track-duration">02:42</span>
                    </div>
                    <!-- Plus de tracks... -->
                </div>
            </div>

            <!-- Playlist 2 -->
            <div class="playlist-item" onclick="togglePlaylist('playlist2')">
                <div class="playlist-header">
                    <div class="playlist-info">
                        <h3>bibeo - promenons nous dans les bois</h3>
                        <p class="playlist-meta">12 tracks • Total Duration: 23:11 • Last Played: Never</p>
                    </div>
                    <div class="playlist-actions">
                        <button class="playlist-play-btn" title="Lire la playlist" onclick="event.stopPropagation()">▶</button>
                        <button class="nfc-btn" title="Associer tag NFC" onclick="event.stopPropagation(); openNfcModal('bibeo - promenons nous dans les bois')">📱</button>
                    </div>
                </div>

                <div class="playlist-upload-zone" onclick="event.stopPropagation(); document.getElementById('fileInput2').click()">
                    <div class="upload-text-small">📁 Ajouter des fichiers</div>
                    <div class="upload-subtext-small">MP3, WAV, FLAC, M4A</div>
                    <input type="file" id="fileInput2" style="display: none;" multiple accept=".mp3,.wav,.flac,.m4a">
                </div>

                <div class="playlist-content" id="playlist2-content">
                    <div class="track-item">
                        <span class="track-number">1</span>
                        <span class="track-name">Compère Guilleri [z9Elu5fu8Co]</span>
                        <span class="track-duration">02:09</span>
                    </div>
                    <div class="track-item">
                        <span class="track-number">2</span>
                        <span class="track-name">Dans la forêt lointaine [ruyTAdmduFs]</span>
                        <span class="track-duration">01:52</span>
                    </div>
                    <!-- Plus de tracks... -->
                </div>
            </div>

            <!-- Playlist 3 -->
            <div class="playlist-item" onclick="togglePlaylist('playlist3')">
                <div class="playlist-header">
                    <div class="playlist-info">
                        <h3>bibeo - les petits poissons...</h3>
                        <p class="playlist-meta">11 tracks • Total Duration: 20:30 • Last Played: Never</p>
                    </div>
                    <div class="playlist-actions">
                        <button class="playlist-play-btn" title="Lire la playlist" onclick="event.stopPropagation()">▶</button>
                        <button class="nfc-btn" title="Associer tag NFC" onclick="event.stopPropagation(); openNfcModal('bibeo - les petits poissons...')">📱</button>
                    </div>
                </div>

                <div class="playlist-upload-zone" onclick="event.stopPropagation(); document.getElementById('fileInput3').click()">
                    <div class="upload-text-small">📁 Ajouter des fichiers</div>
                    <div class="upload-subtext-small">MP3, WAV, FLAC, M4A</div>
                    <input type="file" id="fileInput3" style="display: none;" multiple accept=".mp3,.wav,.flac,.m4a">
                </div>

                <div class="playlist-content" id="playlist3-content">
                    <div class="track-item">
                        <span class="track-number">1</span>
                        <span class="track-name">Il court, il court le furet [073TgB_5TPE]</span>
                        <span class="track-duration">00:51</span>
                    </div>
                    <div class="track-item">
                        <span class="track-number">2</span>
                        <span class="track-name">Le loup, le renard et la belette [sU-UJEfmJbk]</span>
                        <span class="track-duration">02:13</span>
                    </div>

                </div>
            </div>
        </section>
    </div>

    <!-- NFC Modal -->
    <div class="modal-overlay" id="nfcModal">
        <div class="nfc-modal">
            <button class="modal-close" onclick="closeNfcModal()">✕</button>

            <div class="nfc-icon">📱</div>
            <h3 class="nfc-title">nfc.associate_tag</h3>
            <p class="nfc-subtitle">Playlist: <span id="selectedNfcPlaylist"></span></p>

            <div class="nfc-status nfc-waiting">
                <div>🔍 nfc.waiting_for_tag</div>
                <div style="margin-top: 8px; font-size: 12px;">nfc.scanning_status: <span id="scanTime">23:44:01</span></div>
            </div>

            <button class="cancel-btn" onclick="closeNfcModal()">Annuler</button>
        </div>
    </div>

    <script>
        let editMode = false;
        let openPlaylist = null;
        let nfcScanStartTime = null;

        function toggleEditMode() {
            editMode = !editMode;
            const modifyBtn = document.getElementById('modifyBtn');
            const uploadZones = document.querySelectorAll('.playlist-upload-zone');

            if (editMode) {
                modifyBtn.textContent = 'Terminer';
                modifyBtn.classList.add('active');
                uploadZones.forEach(zone => zone.classList.add('show'));
            } else {
                modifyBtn.textContent = 'Modifier';
                modifyBtn.classList.remove('active');
                uploadZones.forEach(zone => zone.classList.remove('show'));
            }
        }

        function togglePlaylist(playlistId) {
            const content = document.getElementById(playlistId + '-content');
            const isCurrentlyOpen = content.classList.contains('show');

            // Fermer toutes les playlists
            document.querySelectorAll('.playlist-content').forEach(el => {
                el.classList.remove('show');
            });

            // Ouvrir la playlist cliquée si elle était fermée
            if (!isCurrentlyOpen) {
                content.classList.add('show');
                openPlaylist = playlistId;
            } else {
                openPlaylist = null;
            }
        }

        function openNfcModal(playlistName) {
            document.getElementById('selectedNfcPlaylist').textContent = playlistName;
            document.getElementById('nfcModal').classList.add('active');
            startNfcScan();
        }

        function closeNfcModal() {
            document.getElementById('nfcModal').classList.remove('active');
            stopNfcScan();
        }

        function startNfcScan() {
            nfcScanStartTime = new Date();
            updateScanTime();
        }

        function stopNfcScan() {
            nfcScanStartTime = null;
        }

        function updateScanTime() {
            if (!nfcScanStartTime) return;

            const now = new Date();
            const diff = Math.floor((now - nfcScanStartTime) / 1000);
            const minutes = Math.floor(diff / 60);
            const seconds = diff % 60;
            const hours = Math.floor(minutes / 60);
            const mins = minutes % 60;

            const timeString = `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            document.getElementById('scanTime').textContent = timeString;

            if (nfcScanStartTime) {
                setTimeout(updateScanTime, 1000);
            }
        }

        // Fermer le modal en cliquant sur l'overlay
        document.getElementById('nfcModal').addEventListener('click', function(event) {
            if (event.target === this) {
                closeNfcModal();
            }
        });

        // Gestionnaires de fichiers
        document.getElementById('fileInput1').addEventListener('change', function(e) {
            handleFileUpload(e.target.files, 'Zelda & Sleep');
        });

        document.getElementById('fileInput2').addEventListener('change', function(e) {
            handleFileUpload(e.target.files, 'bibeo - promenons nous dans les bois');
        });

        document.getElementById('fileInput3').addEventListener('change', function(e) {
            handleFileUpload(e.target.files, 'bibeo - les petits poissons...');
        });

        function handleFileUpload(files, playlistName) {
            if (files.length > 0) {
                const fileNames = Array.from(files).map(f => f.name).join(', ');
                alert(`${files.length} fichier(s) ajouté(s) à "${playlistName}":\n${fileNames}`);
            }
        }
    </script>
</body>
</html>