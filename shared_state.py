from langchain.memory import ConversationBufferMemory


class SharedState:
    """
    Global shared state to persist chat history, vectorstore, and metadata across requests.

    This class is used to maintain memory and document context throughout a session.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        """
        Reset all components of the shared state to their initial values.
        """
        # === Core RAG Components ===
        self.global_text = ""              # Full extracted PDF text
        self.vectorstore = None            # FAISS vector store for chunk retrieval
        self.embeddings_model = None       # Sentence-transformer model
        self.chunks = []                   # Raw text chunks used for embeddings

        # === Metadata ===
        self.uploaded_filename = ""        # PDF file name for page-specific queries
        self.page_count = 0                # Total number of pages in the PDF

        # === Chat Memory ===
        self.chat_history = []             # Stores past user-bot interactions

        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=False
        )

    def add_to_history(self, user_msg: str, bot_msg: str):
        """
        Add a new turn to the conversation history and memory.

        Args:
            user_msg (str): User's input message.
            bot_msg (str): Bot's generated response.
        """
        self.chat_history.append({"user": user_msg, "bot": bot_msg})
        self.memory.chat_memory.add_user_message(user_msg)
        self.memory.chat_memory.add_ai_message(bot_msg)

    def print_chat_history(self):
        """
        Print the entire conversation history to the console.
        Useful for debugging or development.
        """
        print("\n=== Chat History ===")
        if not self.chat_history:
            print("No conversation history yet.")
            return

        for i, turn in enumerate(self.chat_history, 1):
            print(f"\n--- Message {i} ---")
            print(f"User: {turn['user']}")
            print(f"Bot : {turn['bot']}")
        print("====================\n")

    def get_history_as_text(self, last_n: int = 30) -> str:
        """
        Return the last `n` conversation turns as a formatted string.

        Args:
            last_n (int): Number of recent messages to include.

        Returns:
            str: Formatted conversation history for prompt injection or memory context.
        """
        history_slice = self.chat_history[-last_n:]
        return "\n".join(
            f"User: {turn['user']}\nAssistant: {turn['bot']}"
            for turn in history_slice
        )


# === Singleton instance ===
shared_state = SharedState()
