import pygame
import asyncio
import random
import time
import json
from twitchio.ext import commands
from threading import Thread

# I am so fucking sorry for this bullshit of Code. I will make it better in Future

# === Konfiguration ===
TOKEN = 'TOKEN'
TWITCH_NICK = 'NICK'
CHANNEL = 'WZDelchi'
BOT_NAME = 'Fluppy'
STATS_FILE = 'stats.json'

# === Moods und Texturen ===
MOODS = {
    "idle": "textures/pet_idle.png",        
    "happy": "textures/pet_happy.png",      
    "angry": "textures/pet_angry.png",      
    "full": "textures/pet_full.png",        
    "dance": "textures/pet_dance.png",      
    "sleep": "textures/pet_sleep.png",      
    "shy": "textures/pet_shy.png",         
    "reboot": "textures/pet_reboot.png",    
    "laugh": "textures/pet_laugh.png",      
    "annoyed": "textures/pet_annoyed.png",
    "heart": "textures/pet_heart.png",      
    "warn": "textures/pet_warn.png"         
}

current_mood = "idle"
last_user = ""
mood_message = ""
mood_value = 0.0  # -1.0 (angry) bis +1.0 (happy)
sleep_until = 0
reboot_until = 0
global_cooldown = 0
pet_name = BOT_NAME

# === Statistik laden/speichern ===
def load_stats():
    try:
        with open(STATS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_stats():
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f, indent=2)

stats = load_stats()

# === Twitch Bot ===
class Bot(commands.Bot):
    def __init__(self):
        super().__init__(token=TOKEN, prefix='%', initial_channels=[CHANNEL])

    async def event_ready(self):
        print(f"{BOT_NAME} ist online auf Twitch!")

    async def event_message(self, message):
        global current_mood, last_user, mood_message, mood_value
        global sleep_until, reboot_until, global_cooldown, pet_name

        if message.author.name.lower() == BOT_NAME.lower():
            return

        now = time.time()
        user = message.author.name

        if now < global_cooldown or now < sleep_until or now < reboot_until:
            return

        content = message.content.strip()
        parts = content.split()
        if not parts:
            return

        cmd = parts[0].lower()
        args = parts[1:]

        # Stat Tracking
        if user not in stats:
            stats[user] = {}

        def track(command):
            stats[user][command] = stats[user].get(command, 0) + 1
            save_stats()

        if cmd == '%pet':
            current_mood = random.choice(["happy", "angry"])
            mood_value += 0.2 if current_mood == "happy" else -0.2
            mood_message = f"{user} hat {pet_name} gestreichelt!"
            last_user = user
            track('pet')

        elif cmd == '%feed':
            current_mood = "full"
            mood_value += 0.1
            mood_message = f"{user} hat {pet_name} gefüttert."
            last_user = user
            track('feed')

        elif cmd == '%dance':
            current_mood = "dance"
            mood_value += 0.05
            mood_message = f"{user} bringt {pet_name} zum Tanzen!"
            last_user = user
            track('dance')

        elif cmd == '%sleep':
            seconds = int(args[0]) if args and args[0].isdigit() else 30
            seconds = min(seconds, 60)
            current_mood = "sleep"
            sleep_until = now + seconds
            mood_message = f"{user} hat {pet_name} schlafen gelegt ({seconds}s)."
            last_user = user
            track('sleep')

        elif cmd == '%wake':
            sleep_until = 0
            current_mood = "angry"
            mood_value -= 0.3
            mood_message = f"{user} hat {pet_name} geweckt!"
            last_user = user
            track('wake')

        elif cmd == '%hug':
            current_mood = random.choice(["happy", "shy"])
            mood_value += 0.1 if current_mood == "happy" else 0.05
            mood_message = f"{user} hat {pet_name} geknuddelt!"
            last_user = user
            track('hug')

        elif cmd == '%reboot':
            current_mood = "reboot"
            reboot_until = now + 60
            mood_message = f"{user} hat {pet_name} neu gestartet..."
            last_user = user
            track('reboot')

        elif cmd == '%joke':
            current_mood = random.choice(["laugh", "idle"])
            mood_message = f"{user} hat einen Witz erzählt!"
            last_user = user
            track('joke')

        elif cmd == '%boop':
            current_mood = random.choice(["annoyed", "angry"])
            mood_value -= 0.1
            mood_message = f"{user} hat {pet_name} geboopt."
            last_user = user
            track('boop')

        elif cmd == '%love':
            percent = random.randint(0, 100)
            current_mood = "heart"
            mood_message = f"{user} liebt {pet_name} zu {percent}% ❤️"
            last_user = user
            track('love')

        elif cmd == '%warn':
            current_mood = "warn"
            mood_message = f"{user} hat eine Warnung ausgegeben!"
            last_user = user
            track('warn')

        elif cmd == '%name' and args:
            pet_name = args[0]
            mood_message = f"{user} hat den Namen geändert zu {pet_name}"
            last_user = user
            track('name')

        elif cmd == '%help':
            await message.channel.send("Alle Commands und Quellcode: https://github.com/1206Elchi/FluppyGame/blob/main/ReadMe.md")
            track('help')

        global_cooldown = now + 3

# === Anzeige ===
def show_pet():
    global current_mood, last_user, mood_message, mood_value

    pygame.init()
    screen = pygame.display.set_mode((400, 400), pygame.RESIZABLE)
    font = pygame.font.SysFont("arial", 24)
    clock = pygame.time.Clock()

    raw_textures = {mood: pygame.image.load(path) for mood, path in MOODS.items()}
    scaled_textures = {}

    def rescale_textures(w, h):
        for mood, img in raw_textures.items():
            height = int(h * 0.6)
            width = int(img.get_width() * (height / img.get_height()))
            scaled_textures[mood] = pygame.transform.scale(img, (width, height))

    rescale_textures(400, 400)

    while True:
        screen.fill((255, 255, 255))
        width, height = screen.get_size()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.VIDEORESIZE:
                rescale_textures(event.w, event.h)

        # Mood langsam zurück zur Mitte
        if abs(mood_value) > 0.01:
            mood_value *= 0.99
        else:
            mood_value = 0.0

        img = scaled_textures.get(current_mood, scaled_textures["idle"])
        img_rect = img.get_rect(center=(width // 2, height // 2 - 20))
        screen.blit(img, img_rect)

        name_text = font.render(f"{pet_name}", True, (0, 0, 0))
        screen.blit(name_text, (width // 2 - name_text.get_width() // 2, 10))

        if mood_message:
            msg_text = font.render(mood_message, True, (30, 30, 30))
            screen.blit(msg_text, (width // 2 - msg_text.get_width() // 2, height - 40))

        pygame.display.flip()
        clock.tick(30)

# === Start ===
Thread(target=show_pet).start()
bot = Bot()
bot.run()
