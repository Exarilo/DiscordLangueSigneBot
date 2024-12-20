import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from bs4 import BeautifulSoup
import os
from flask import Flask, render_template
from threading import Thread

app = Flask(__name__)


@app.route('/')
def index():
    return "Alive"


def run():
    app.run(host='0.0.0.0', port=8080)


def keep_alive():
    t = Thread(target=run)
    t.start()


DISCORD_TOKEN = os.getenv("TOKEN")
keep_alive()


class DiscordBot(commands.Bot):

    def __init__(self):
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.synced = False

    async def setup_hook(self):
        if not self.synced:
            try:
                await self.tree.sync()
                self.synced = True
            except Exception as e:
                print(f"Erreur de synchronisation des commandes : {e}")

    async def on_ready(self):
        print(f"Bot connecté en tant que {self.user}")
        print(
            f"Commandes disponibles : {[cmd.name for cmd in self.tree.get_commands()]}"
        )


async def fetch_html_content(url):
    """1er contenu HTML -> todo voir si plus de videos."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    return None
        except aiohttp.ClientError:
            return None


def extract_video_src(html):
    if not html:
        return None
    soup = BeautifulSoup(html, 'html.parser')
    video_tag = soup.find('video')
    if video_tag and video_tag.get('src'):
        return video_tag['src']
    return None


bot = DiscordBot()


@bot.tree.command(name="signe", description="Trouve le signe associé au mot")
@app_commands.describe(word="Mot à chercher dans le dictionnaire ")
async def signe(interaction: discord.Interaction, word: str):
    await interaction.response.defer()
    base_url = "https://dico.elix-lsf.fr/dictionnaire/"
    full_url = base_url + word

    html_content = await fetch_html_content(full_url)
    if not html_content:
        await interaction.followup.send(
            "Impossible de récupérer le contenu de la page. 😭")
        return

    video_url = extract_video_src(html_content)
    if video_url:
        await interaction.followup.send(video_url)
    else:
        await interaction.followup.send("Aucune vidéo trouvée pour ce mot. 😢")


bot.run(DISCORD_TOKEN)
