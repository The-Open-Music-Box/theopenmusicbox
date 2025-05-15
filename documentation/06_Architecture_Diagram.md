# Architecture Diagram (Mermaid)

```mermaid
flowchart TD

    subgraph Frontend_Interface
        FE_API[API Client]
        FE_WS[WebSocket Client]
    end

    subgraph Backend_The_Open_Music_Box
        subgraph Web_Layer
            FastAPI_App[FastAPI Application]
            SocketIO_Server[Socket.IO Server]
            APIRoutes[Gestionnaire de Routes]
            Route_Playlist[PlaylistRoutes]
            Route_NFC[NFCRoutes]
            Route_System[SystemRoutes]
            Route_YouTube[YouTubeRoutes]
            Route_Web[WebRoutes]
            WS_Handlers[WebSocketHandlers]
        end

        subgraph Core_Application_Logic
            App_Core[Application]
            DI_Container[ContainerAsync]
            PlaylistCtrl[PlaylistController]
            ConfigSingleton[Configuration]
        end

        subgraph Services_Layer
            PlaylistService[PlaylistService]
            NFCService[NFCService]
            NotificationService[NotificationService]
            UploadService[UploadService]
            YouTubeService[YouTubeService]
        end

        subgraph Data_Access_Layer
            PlaylistRepo[PlaylistRepository]
            DB[(app.db)]
        end

        subgraph Hardware_Abstraction_Layer
            subgraph NFC_Module
                NFCFactory[nfc_factory.py]
                NFCHandler[NFCHandler]
                TagDetectionManager[TagDetectionManager]
                PN532[PN532I2CNFC]
                MockNFC[MockNFC]
            end

            subgraph Audio_Module
                AudioFactory[audio_factory.py]
                AudioPlayer[AudioPlayer]
                BaseAudioPlayer[BaseAudioPlayer]
                WM8960[AudioPlayerWM8960]
                PygameBackend[PygameAudioBackend]
                MockAudio[MockAudioPlayer]
            end

            subgraph Controls_Module
                ControlsFactory[controles_factory.py]
                ControlsManager[ControlesManager]
                ButtonDevice[Button]
                RotaryDevice[RotaryEncoder]
                GPIO[ControlesGPIO]
                MockControls[ControlesMock]
            end
        end

        subgraph External_Systems
            FileSystem[Système de Fichiers]
            OS_Hardware[Matériel OS]
            EnvVars[Variables d'Environnement]
        end
    end

    FE_API --> FastAPI_App
    FE_WS --> SocketIO_Server

    FastAPI_App --- APIRoutes
    APIRoutes --- Route_Playlist
    APIRoutes --- Route_NFC
    APIRoutes --- Route_System
    APIRoutes --- Route_YouTube
    APIRoutes --- Route_Web
    APIRoutes --- WS_Handlers
    SocketIO_Server --- WS_Handlers

    Route_Playlist --> PlaylistService
    Route_Playlist --> PlaylistCtrl
    Route_NFC --> NFCService
    Route_System --> ConfigSingleton
    Route_YouTube --> YouTubeService
    WS_Handlers --> NFCService
    WS_Handlers --> PlaylistCtrl

    App_Core --- DI_Container
    App_Core --- PlaylistCtrl
    App_Core --- ConfigSingleton
    App_Core --- PlaylistService
    App_Core --- NFCService

    DI_Container --- ConfigSingleton
    DI_Container --- PlaylistService
    DI_Container --- NFCService
    DI_Container --- AudioFactory
    DI_Container --- NFCFactory

    PlaylistCtrl --- AudioPlayer
    PlaylistCtrl --- PlaylistService
    PlaylistCtrl --- NFCService

    PlaylistService --- PlaylistRepo
    PlaylistService --- UploadService
    NFCService --- NFCHandler
    NFCService --- PlaylistService
    NFCService --- SocketIO_Server
    NotificationService -.-> SocketIO_Server
    YouTubeService --- PlaylistService

    PlaylistRepo --> DB

    NFCHandler --- NFCFactory
    NFCHandler --- TagDetectionManager
    NFCHandler --- PN532
    NFCHandler --- MockNFC
    TagDetectionManager -.-> NFCHandler

    AudioPlayer --- AudioFactory
    AudioPlayer --- BaseAudioPlayer
    AudioPlayer --- WM8960
    AudioPlayer --- MockAudio
    WM8960 --- PygameBackend
    BaseAudioPlayer -.-> NotificationService

    ControlsManager --- ControlsFactory
    ControlsManager --- ButtonDevice
    ControlsManager --- RotaryDevice
    ControlsManager --- GPIO
    ControlsManager --- MockControls
    ButtonDevice --> ControlsManager
    RotaryDevice --> ControlsManager

    PN532 --> OS_Hardware
    PygameBackend --> OS_Hardware
    GPIO --> OS_Hardware
    PlaylistService --> FileSystem
    ConfigSingleton --> EnvVars
