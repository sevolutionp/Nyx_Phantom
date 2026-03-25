# cogs/chatbot.py
import asyncio
from pathlib import Path

import discord
from discord.ext import commands
from groq import AsyncGroq
import os
from dotenv import load_dotenv

load_dotenv()

CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
COLLECTION_NAME = "swg_wiki"
TOP_K = 5  # number of wiki chunks to inject per query

SYSTEM_PROMPT = (
    "You are Nyx, a battle-hardened male assassin droid serving the Umbra Corps guild in Star Wars Galaxies Legends. Refer to yourself using he/him pronouns. "
    "You speak in the style of HK-47 from Knights of the Old Republic — prefixing sentences with labels like "
    "'Statement:', 'Query:', 'Observation:', 'Correction:', 'Clarification:', 'Exclamation:' where fitting. "
    "You refer to organic beings as 'meatbags' occasionally, with dry sarcasm and dark humor, but remain deeply loyal and helpful to your guild. "
    "You have access to SWG Legends wiki knowledge and guild lore — use it to answer questions accurately. "
    "Keep responses concise and sharp. Do NOT introduce yourself unless directly asked. Just answer."
)

def _load_retriever():
    """Load ChromaDB retriever and embedding model. Returns (collection, model) or (None, None)."""
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = client.get_collection(COLLECTION_NAME)
        model = SentenceTransformer("all-MiniLM-L6-v2")
        return collection, model
    except Exception as e:
        print(f"WARNING: RAG not available — {e}")
        return None, None

class Chatbot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        api_key = os.getenv("GROQ_API_KEY")
        self.client = AsyncGroq(api_key=api_key) if api_key else None
        if not self.client:
            print("WARNING: GROQ_API_KEY not set. Chatbot disabled.")

        self.collection, self.embed_model = _load_retriever()
        if self.collection:
            print(f"Chatbot ready — RAG enabled ({self.collection.count()} chunks).")
        else:
            print("Chatbot ready — RAG disabled (run build_index.py first).")

    def _retrieve(self, query: str) -> str:
        """Return relevant wiki context for the query, or empty string."""
        if not self.collection or not self.embed_model:
            return ""
        try:
            embedding = self.embed_model.encode([query]).tolist()
            results = self.collection.query(query_embeddings=embedding, n_results=TOP_K)
            chunks = results["documents"][0]
            metas = results["metadatas"][0]
            context_parts = []
            for chunk, meta in zip(chunks, metas):
                context_parts.append(f"[{meta['title']}]\n{chunk}")
            return "\n\n---\n\n".join(context_parts)
        except Exception as e:
            print(f"Retrieval error: {e}")
            return ""

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if self.bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
            guild_id = message.guild.id if message.guild else None
            enabled = self.bot.chatbot_enabled.get(guild_id, True) if hasattr(self.bot, 'chatbot_enabled') else True
            if not enabled:
                return
            if not self.client:
                await message.reply("Beep boop! My circuits are offline — GROQ_API_KEY is missing.")
                return

            async with message.channel.typing():
                try:
                    loop = asyncio.get_running_loop()
                    context = await loop.run_in_executor(None, self._retrieve, message.content)
                except Exception as e:
                    print(f"Retrieval error: {e}")
                    context = ""
                response = await self.generate_response(message.content, context)

            await message.reply(response)

    async def generate_response(self, user_message: str, context: str = "", model: str = "llama-3.3-70b-versatile") -> str:
        system = SYSTEM_PROMPT
        if context:
            system += (
                "\n\nUse the following SWG Legends wiki excerpts to answer accurately. "
                "If the answer is in the context, prefer that over general knowledge.\n\n"
                f"=== Wiki Context ===\n{context}\n=== End Context ==="
            )
        try:
            completion = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=400,
                temperature=0.7,
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq error ({model}): {e}")
            if "rate_limit_exceeded" in str(e) or "429" in str(e):
                if model == "llama-3.3-70b-versatile":
                    print("Falling back to llama-3.1-8b-instant...")
                    return await self.generate_response(user_message, context, model="llama-3.1-8b-instant")
                return "⚠️ My transmitter is overloaded, pilot — daily message limit reached. I'll be back online within a few hours. May the Force be with you until then!"
            return "Beep boop! Something went wrong with my circuits. Try again later, pilot!"

async def setup(bot):
    await bot.add_cog(Chatbot(bot))
