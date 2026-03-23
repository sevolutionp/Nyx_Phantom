# cogs/lore_scraper.py — Scrapes a Discord channel into the RAG lore index
import asyncio
import io
import os
from datetime import timezone
from pathlib import Path

import chromadb
import discord
import httpx
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

load_dotenv()

CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
COLLECTION_NAME = "swg_wiki"
EMBED_MODEL = "all-MiniLM-L6-v2"
OWNER_ID = int(os.getenv("BOT_OWNER_ID"))
ALLOWED_ROLES = ["Leader", "Militia", "Officer", "Senior Officer", "Council Member"]

MESSAGE_LIMIT = 2000
CHUNK_SIZE = 800


def chunk_text(text: str, size: int = CHUNK_SIZE) -> list[str]:
    """Split text into chunks of roughly `size` characters."""
    chunks = []
    while len(text) > size:
        split = text.rfind("\n", 0, size)
        if split == -1:
            split = size
        chunks.append(text[:split].strip())
        text = text[split:].strip()
    if text:
        chunks.append(text)
    return chunks


def chunk_messages(messages: list[dict], size: int = CHUNK_SIZE) -> list[str]:
    """Group consecutive messages into text chunks."""
    chunks = []
    current = ""
    for msg in messages:
        line = f"[{msg['author']}]: {msg['content']}\n"
        if len(current) + len(line) > size:
            if current:
                chunks.append(current.strip())
            current = line
        else:
            current += line
    if current:
        chunks.append(current.strip())
    return chunks


async def extract_pdf_text(url: str) -> str | None:
    """Download a PDF from a URL and extract its text."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url)
            resp.raise_for_status()
        reader = PdfReader(io.BytesIO(resp.content))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(p for p in pages if p.strip())
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return None


class LoreScraper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._model = None
        self._collection = None

    def _get_db(self):
        if self._collection is None:
            client = chromadb.PersistentClient(path=str(CHROMA_DIR))
            self._collection = client.get_or_create_collection(
                COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection

    def _get_model(self):
        if self._model is None:
            self._model = SentenceTransformer(EMBED_MODEL)
        return self._model

    def _is_authorized(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == OWNER_ID:
            return True
        user_roles = [r.name for r in interaction.user.roles]
        return any(r in ALLOWED_ROLES for r in user_roles)

    @app_commands.command(name="scrape-lore", description="Index this channel's history and any PDFs into Nyx's knowledge base")
    async def scrape_lore(self, interaction: discord.Interaction):
        if not self._is_authorized(interaction):
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return

        await interaction.response.send_message(
            f"📡 Scanning **#{interaction.channel.name}**... this may take a moment.",
            ephemeral=True
        )

        channel = interaction.channel
        guild_name = interaction.guild.name if interaction.guild else "DM"
        channel_name = channel.name

        raw_messages = []
        pdf_attachments = []

        async for msg in channel.history(limit=MESSAGE_LIMIT, oldest_first=True):
            # Collect text messages
            if not msg.author.bot and msg.content.strip():
                raw_messages.append({
                    "author": msg.author.display_name,
                    "content": msg.content.strip(),
                })
            # Collect PDF attachments
            for attachment in msg.attachments:
                if attachment.filename.lower().endswith(".pdf"):
                    pdf_attachments.append({
                        "url": attachment.url,
                        "filename": attachment.filename,
                    })

        # Extract PDF text
        pdf_chunks = []
        for pdf in pdf_attachments:
            print(f"Extracting PDF: {pdf['filename']}")
            text = await extract_pdf_text(pdf["url"])
            if text:
                for i, chunk in enumerate(chunk_text(text)):
                    pdf_chunks.append({
                        "id": f"pdf_{guild_name}_{pdf['filename']}_{i}".replace(" ", "_"),
                        "text": chunk,
                        "meta": {
                            "title": f"{pdf['filename']} (PDF)",
                            "url": pdf["url"],
                            "chunk": i,
                            "source": "pdf",
                        }
                    })

        msg_chunks = chunk_messages(raw_messages)

        if not msg_chunks and not pdf_chunks:
            await interaction.followup.send("⚠️ No readable content found in this channel.", ephemeral=True)
            return

        def _index():
            model = self._get_model()
            collection = self._get_db()

            doc_ids, doc_texts, doc_metas = [], [], []

            for i, chunk in enumerate(msg_chunks):
                doc_ids.append(f"discord_{guild_name}_{channel_name}_{i}".replace(" ", "_"))
                doc_texts.append(chunk)
                doc_metas.append({
                    "title": f"{guild_name} #{channel_name}",
                    "url": f"discord://channel/{channel.id}",
                    "chunk": i,
                    "source": "discord",
                })

            for item in pdf_chunks:
                doc_ids.append(item["id"])
                doc_texts.append(item["text"])
                doc_metas.append(item["meta"])

            embeddings = model.encode(doc_texts, batch_size=64).tolist()
            collection.upsert(ids=doc_ids, documents=doc_texts, embeddings=embeddings, metadatas=doc_metas)
            return len(doc_texts)

        loop = asyncio.get_running_loop()
        total = await loop.run_in_executor(None, _index)

        summary = f"✅ **#{channel_name}** indexed! "
        if raw_messages:
            summary += f"{len(raw_messages)} messages"
        if pdf_attachments:
            summary += f" + {len(pdf_attachments)} PDF(s)"
        summary += f" → {total} chunks added to Nyx's knowledge base."

        await interaction.followup.send(summary, ephemeral=True)
        print(f"Lore indexed: #{channel_name} ({guild_name}) — {len(raw_messages)} msgs, {len(pdf_attachments)} PDFs, {total} chunks")


async def setup(bot):
    await bot.add_cog(LoreScraper(bot))
