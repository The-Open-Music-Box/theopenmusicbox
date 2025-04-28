/**
 * French translations
 */

export default {
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
  navigation: {
    home: 'Accueil',
    about: 'À propos',
    contact: 'Contact',
    upload: 'Téléverser',
    library: 'Bibliothèque',
  },
  stats: {
    generalInfo: 'Informations Générales',
    systemStatus: 'État du Système',
    battery: 'Batterie',
    trackCount: 'Nombre de morceaux',
    freeSpace: 'Espace libre',
    lastUpdate: 'Dernière mise à jour',
  },
  contact: {
    getInTouch: 'Contactez-nous',
    firstName: 'Prénom',
    lastName: 'Nom',
    email: 'Email',
    phone: 'Numéro de téléphone',
    message: 'Message',
    sendMessage: 'Envoyer le message',
    sending: 'Envoi en cours...',
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
