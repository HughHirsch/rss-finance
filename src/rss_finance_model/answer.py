"""Answer a question from retrieved chunks with a local chat model via Ollama.

Responsibility: build the prompt, call the model, and return the answer together with the
sources it cites.

Decisions:
- Grounding: tell the model to answer only from the provided articles, and to say so when
  they don't contain the answer.
- Citations: number the chunks in the prompt, ask for [1]-style references, then map those
  numbers back to URLs. What happens if the model cites a number that doesn't exist?
- Dates: include each article's published time and today's date in the prompt; "latest"
  questions depend on both.
- Streaming the answer vs. waiting for the full response.
- Context budget: how many chunks fit in the chat model's context with room for the answer.

Docs: https://github.com/ollama/ollama-python
"""
