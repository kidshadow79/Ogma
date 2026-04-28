# Capability Advisor — The AI That Knows When to Use Its Tools

**Verified source**: `extensions/capability_advisor/__init__.py`

> French version: [../../fr/extensions/06_capability_advisor.md](../../fr/extensions/06_capability_advisor.md)

---

## Concept

OGMA has several special capabilities (memorize, introspect, generate images, see via webcam, search the internet, consult a biography). Without guidance, the AI might forget to use the right capability at the right moment.

The Capability Advisor solves this problem: for each message, the Archivist analyzes the context and **suggests a relevant capability** if the context justifies it. This suggestion appears as an LED in the interface, and is transmitted to the main AI as a discreet piece of advice.

---

## The 6 managed capabilities

| Icon | Capability | Typical trigger |
|---|---|---|
| 💾 | Memorization | Important information to remember |
| 🧠 | Introspection | Question about the AI itself |
| 🎨 | Image generation | Visualization request |
| 📷 | Webcam vision | Relevant visual context |
| 🌐 | Web search | Need for recent information |
| 👤 | Biography | Personal question about the user |

---

## Workflow

1. User message received
2. Archivist analyzes the message (context, intent, recent history)
3. If relevant context detected → suggestion of ONE capability (not systematic)
4. Corresponding LED lights up in the header
5. A concise piece of advice is injected into the main AI's context
6. LED turns off after effective use of the capability

---

## Philosophy

The Capability Advisor never forces anything. It suggests. The main AI decides whether to follow the advice or not. This approach avoids mechanical tool use and preserves the natural character of the conversation.
