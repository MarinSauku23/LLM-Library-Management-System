let chatOpen = false;

// opens/closes the chatbot panel

function toggleChat() {
  const panel = document.getElementById("chatbot-panel");
  chatOpen = !chatOpen;
  panel.style.display = chatOpen ? "flex" : "none";

  // focuses the input for faster typing when opening
  if (chatOpen) {
    const input = document.getElementById("chatbot-input");
    input.focus();
  }
}


// appends a message bubble to the chat window
function appendMessage(text, who) {
  const messages = document.getElementById("chatbot-messages");
  if (!messages) return; // safety

  const row = document.createElement("div");
  row.className = "msg-row " + (who === "user" ? "user" : "bot");

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble " + (who === "user" ? "user" : "bot");
  bubble.textContent = text;

  row.appendChild(bubble);
  messages.appendChild(row);

  // keeps the latest message in view
  messages.scrollTop = messages.scrollHeight;
}


// sends the user's message to the backend (/ai-chat) and displays the reply
async function sendChat() {
  const input = document.getElementById("chatbot-input");
  if (!input) return; // safety

  const text = input.value.trim();
  if (!text) return;

  appendMessage(text, "user");
  input.value = "";

  try {
    const res = await fetch("/ai-chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });

    // non-200 response: shows status code/text for debugging
    if (!res.ok) {
      const errText = await res.text();
      appendMessage("Server error: " + errText, "bot");
      return;
    }

    const data = await res.json();


    const reply = data.reply || "Sorry, something went wrong.";
    appendMessage(reply, "bot");
  } catch (err) {
    console.error(err);
    appendMessage("Network error. Please try again.", "bot");
  }
}

// sends message when enter is pressed while the chatbot input is focused
document.addEventListener("keydown", function (e) {
  if (
    chatOpen &&
    e.key === "Enter" &&
    document.activeElement.id === "chatbot-input"
  ) {
    e.preventDefault();
    sendChat();
  }
});
