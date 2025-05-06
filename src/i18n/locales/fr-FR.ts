/**
 * French translations
 */

export default {
  navigation: {
    home: 'Accueil',
    about: 'À propos',
    contact: 'Contact',
    settings: 'Réglages',
  },
  settings: {
    title: 'Réglages',
    language: 'Langue',
    locales: {
      'en-US': 'Anglais',
      'fr-FR': 'Français',
    },
  },
  contact: {
    getInTouch: 'Contactez-nous',
    firstName: 'Prénom',
    lastName: 'Nom',
    email: 'Email',
    phone: 'Numéro de téléphone',
    message: 'Message',
    send: 'Envoyer',
    emailValue: 'hi@theopenmusicbox.com',
    website: 'Site web',
    websiteUrl: 'theopenmusicbox.com',
    bsky: 'Bluesky',
    bskyUrl: 'bsky.app/profile/theopenmusicbox.com',
    facebook: 'Facebook',
    facebookUrl: 'facebook.com/theopenmusicbox',
    github: 'GitHub',
    githubUrl: 'github.com/The-Open-Music-Box/firmware',
  },
  nfc: {
    NFC_OK: 'Lecteur NFC prêt',
    NFC_NOT_AVAILABLE: 'Lecteur NFC non disponible',
  },
  common: {
    link: 'Lier',
    loading: 'Chargement...',
    error: 'Erreur',
    success: 'Succès',
    cancel: 'Annuler',
    confirm: 'Confirmer',
    delete: 'Supprimer',
    save: 'Enregistrer',
    edit: 'Modifier',
    add: 'Ajouter',
    upload: 'Télécharger',
    submit: 'Envoyer',
    sendMessage: 'Envoyer un message',
    socketError: 'Erreur de connexion socket !',
    fallbackToMock: 'Impossible de se connecter au serveur. Utilisation de données simulées.',
  },
  upload: {
    dragDrop: 'ou glisser-déposer',
    fileType: 'Fichiers audio uniquement',
    uploadFile: 'Télécharger un fichier',
    copyingFiles: 'Copie des fichiers',
    progress: 'Progression du téléchargement',
    validationError: 'Erreur de validation du fichier',
    uploadError: 'Échec du téléchargement',
    fileTooLarge: 'Le fichier est trop volumineux. La taille maximale est de {size}MB',
    invalidFileType: 'Type de fichier invalide. Seuls les fichiers audio sont acceptés',
  },
  audio: {
    duration: 'Durée',
    plays: 'Lectures',
    noTrackSelected: 'Aucun morceau sélectionné',
  },
  track: {
    delete: {
      title: 'Supprimer le morceau',
      confirmation: 'Êtes-vous sûr de vouloir supprimer le morceau "{title}" de la playlist "{playlist}" ? Cette action ne peut pas être annulée.',
      untitled: 'sans titre',
      unnamed: 'sans nom',
    }
  },
  player: {
    previous: 'Morceau précédent',
    next: 'Morceau suivant',
    rewind: 'Reculer de 10 secondes',
    skip: 'Avancer de 10 secondes',
    playPause: 'Lecture/Pause',
  },

  stats: {
    generalInfo: 'Informations Générales',
    systemStatus: 'État du Système',
    battery: 'Batterie',
    trackCount: 'Nombre de morceaux',
    freeSpace: 'Espace libre',
    lastUpdate: 'Dernière mise à jour',
  },

  file: {
    listTitle: 'Liste des fichiers audio',
    associateTag: 'Associer un tag',
    openOptions: 'Ouvrir les options',
    status: {
      pending: 'En attente',
      processing: 'En traitement',
      ready: 'Prêt',
      error: 'Erreur',
    },
    tracks: 'morceaux',
    lastPlayed: 'Dernière lecture',
    errorLoading: 'Erreur lors du chargement des playlists',
    errorDeleting: 'Erreur lors de la suppression du morceau',
  },
};
