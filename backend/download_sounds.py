import os
import urllib.request

sounds_dir = os.path.join("admin", "public", "sounds")
os.makedirs(sounds_dir, exist_ok=True)

# Список звуков и их URL (бесплатные короткие звуки с GitHub или открытых источников)
sounds = {
    "bell.mp3": "https://raw.githubusercontent.com/ionden/ion.sound/master/sounds/bell_ring.mp3",
    "cash.mp3": "https://raw.githubusercontent.com/ionden/ion.sound/master/sounds/button_tiny.mp3",
    "chime.mp3": "https://raw.githubusercontent.com/ionden/ion.sound/master/sounds/glass.mp3",
    "sonar.mp3": "https://raw.githubusercontent.com/ionden/ion.sound/master/sounds/camera_flashing_2.mp3",
    "water.mp3": "https://raw.githubusercontent.com/ionden/ion.sound/master/sounds/water_droplet.mp3",
    "click.mp3": "https://raw.githubusercontent.com/ionden/ion.sound/master/sounds/button_click.mp3",
    "branch.mp3": "https://raw.githubusercontent.com/ionden/ion.sound/master/sounds/branch_break.mp3",
    "push.mp3": "https://raw.githubusercontent.com/ionden/ion.sound/master/sounds/button_push.mp3",
    "doorbell.mp3": "https://raw.githubusercontent.com/ionden/ion.sound/master/sounds/door_bell.mp3",
    "error.mp3": "https://raw.githubusercontent.com/ionden/ion.sound/master/sounds/computer_error.mp3"
}

for name, url in sounds.items():
    path = os.path.join(sounds_dir, name)
    print(f"Downloading {name} to {path}...")
    try:
        urllib.request.urlretrieve(url, path)
        print(f"Successfully downloaded {name}")
    except Exception as e:
        print(f"Failed to download {name}: {e}")
