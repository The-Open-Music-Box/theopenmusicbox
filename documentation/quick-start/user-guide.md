# Quick Start Guide - Users

## Get Your Music Box Running in 15 Minutes

This guide helps you set up and start using The Open Music Box quickly, whether you're building from scratch or setting up a pre-built device.

## What You'll Need

### Essential Components
- ✅ Raspberry Pi (4B recommended, Zero 2W minimum)
- ✅ MicroSD card (32GB+, flashed with our image)
- ✅ Power supply (5V 3A for Pi 4, 5V 2.5A for Pi Zero)
- ✅ WiFi network access
- ✅ Computer or smartphone for setup

### Optional but Recommended
- 🎵 WM8960 Audio HAT + speakers (better sound quality)
- 🏷️ NFC tags and RC522 reader (tap-to-play functionality)
- 🔘 Physical controls (buttons, rotary encoder)
- 🔋 Battery pack for portability

## Step 1: Hardware Setup (5 minutes)

### Basic Assembly
1. **Insert SD Card**: Pre-flashed with Open Music Box OS
2. **Connect Audio**:
   - **Basic**: 3.5mm speakers/headphones to Pi audio jack
   - **Enhanced**: WM8960 HAT with connected speakers
3. **Connect Power**: Use appropriate power supply for your Pi model
4. **First Boot**: Wait 2-3 minutes for initial setup

### Network Connection
The device will automatically:
- ✅ Create a WiFi hotspot named `OpenMusicBox-Setup`
- ✅ Allow configuration via web interface
- ✅ Connect to your home WiFi network

## Step 2: Connect to Your Music Box (3 minutes)

### Find Your Device

**Option A: Automatic Discovery**
```
Open your web browser and go to:
http://openmusicbox.local:5004
```

**Option B: WiFi Setup Mode**
If automatic discovery doesn't work:
1. Connect to WiFi network: `OpenMusicBox-Setup`
2. Open browser to: `http://192.168.4.1:5004`
3. Complete WiFi configuration
4. Device will restart and connect to your home network

### Access the Web Interface
Once connected, you should see:
- 🎵 **Welcome Screen** with system status
- 📁 **Empty Playlists** section (ready for your music)
- ⚙️ **Settings** button in top-right corner
- 🔊 **Audio Player** (hidden until music is loaded)

## Step 3: Add Your First Music (5 minutes)

### Upload Music Files

1. **Click "Edit Mode"** toggle (top-right corner)
2. **Create a New Playlist**:
   - Click the "+" button
   - Name it "My First Playlist"
   - Click "Create"

3. **Add Music Files**:
   - Drag and drop MP3/FLAC/WAV files onto the playlist
   - OR click "Upload Files" button and select files
   - Watch the upload progress bar

**Supported formats**: MP3, FLAC, WAV, M4A, OGG

### Alternative: YouTube Downloads
1. **Enable Edit Mode**
2. **Click YouTube icon** on any playlist
3. **Search for music** or paste YouTube URL
4. **Click Download** - the track will be added automatically

## Step 4: Start Playing Music (2 minutes)

### Basic Playback
1. **Click the Play button** (▶️) next to any playlist
2. **Music should start playing** immediately
3. **Use the player controls**:
   - ⏯️ **Play/Pause**: Toggle playback
   - ⏮️ **Previous**: Go to previous track
   - ⏭️ **Next**: Go to next track
   - 🔊 **Volume**: Adjust audio level
   - 🔀 **Seek**: Click on progress bar to jump to position

### Test Audio Output
If no sound:
1. **Check volume levels** (both system and app)
2. **Try different audio output** in Settings
3. **Test with different music file**
4. **Verify speaker connections**

## Step 5: Set Up NFC Tags (Optional, 3 minutes)

If you have NFC tags and reader:

### Tag Association
1. **Click "Link NFC"** button next to a playlist
2. **Hold NFC tag** near the reader (within 2cm)
3. **Wait for confirmation** - LED will turn green
4. **Test**: Remove and re-scan tag - music should start!

### Tag Management
- **Override existing tags**: System will ask for confirmation
- **Remove associations**: Click "Unlink NFC" to remove tag association
- **Multiple tags**: Each playlist can have one tag, each tag links to one playlist

## Quick Troubleshooting

### No Audio Output
```
✅ Check speaker connections
✅ Verify volume levels (not muted)
✅ Test different audio files
✅ Check Settings > Audio Output
```

### Can't Connect to Device
```
✅ Verify power LED is on
✅ Wait 3+ minutes after power-on
✅ Check WiFi network name "OpenMusicBox-Setup"
✅ Try direct IP: http://192.168.1.100:5004
```

### Music Upload Fails
```
✅ Check file format (MP3, FLAC, WAV supported)
✅ Verify file size (<100MB per file)
✅ Ensure stable network connection
✅ Try smaller files first
```

### NFC Tags Not Working
```
✅ Verify NFC reader is connected properly
✅ Check tag compatibility (NTAG213/215/216)
✅ Hold tag within 2cm of reader
✅ Try different tags
```

## Next Steps

### Customize Your Experience
- **Create themed playlists**: Kids songs, bedtime stories, etc.
- **Add album art**: Upload images for visual playlist identification
- **Set up multiple rooms**: Connect multiple devices for house-wide music
- **Configure parental controls**: Time limits and content filtering

### Advanced Features
- **Physical controls**: Add buttons and rotary encoders
- **Battery power**: Make it portable with battery pack
- **Custom enclosure**: 3D print or build custom housing
- **Voice control**: Integrate with voice assistants

### Get Help
- **Web Interface Help**: Click "?" icon for context-sensitive help
- **System Status**: Settings > System Info for diagnostic information
- **Update Software**: Settings > Updates for latest features
- **Community**: Join our Discord/Forum for user support

## Pro Tips

### Playlist Organization
```
✨ Use descriptive names: "Morning Energy", "Bedtime Stories"
✨ Keep playlists focused: 10-20 tracks work best
✨ Organize by mood or activity, not just genre
✨ Create "Favorites" playlist for most-played songs
```

### NFC Tag Tips
```
🏷️ Use different colored tags for different moods
🏷️ Write playlist name on tag with permanent marker
🏷️ Store backup tags - they can break or get lost
🏷️ Test tags regularly to ensure they still work
```

### Performance Tips
```
⚡ Use high-quality SD cards (Class 10, U1 minimum)
⚡ Keep software updated for best performance
⚡ Restart device weekly for optimal performance
⚡ Monitor storage space - keep 25% free
```

## What's Next?

You now have a fully functional music player! Explore these additional features:

- 📱 **Mobile App**: Download our companion app for remote control
- 🎨 **Themes**: Customize the interface with different color schemes
- 👨‍👩‍👧‍👦 **Family Features**: Set up multiple user profiles
- 📊 **Analytics**: Track listening habits and favorite songs
- 🔊 **Multi-room**: Sync playback across multiple devices

**Enjoy your Open Music Box!** 🎵

---

*Need more help? Check out our [detailed documentation](../README.md) or join the community discussion forums.*