# lucas
Llm Unified Coding ASsistant

## Intro

In progress effort to experiment on efficient real-world software engineering tasks resolution.


* Focus on making changes to medium-sized codebases, where change is spread across multiple files. No autocomplete or generating snake game for 101th time.
* Human readable indexing with LLMs, which can be debugged and understood - no multidimensional vector stores.
* Focus on patch generation/application, not generating entire files from scratch to improve cost/latency.
* Support for local models (llama.cpp server) and remote LLM providers (claude, mistral, groq, cerebras).



## Example

We'll use this repository as example.

First, you create configuration file (lucas.conf) :

```
{
    "chunk_size": 4096,
    "llm_client": {"type": "GroqClient"},
    "query_client": {
        "type": "ClaudeClient",
        "model": "claude-3-5-sonnet-20240620",
        "max_tokens": 6144,
        "tokens_rate": 200000,
        "cache": "ephemeral"
    },
    "crawler": {"includes": "*.py,*.json,*.txt", "traverse": "git"},
    "token_counter" : {"type": "local_counter", "endpoint": "http://localhost:8080/tokenize"}
}
```

We need to configure two separate llm clients:
1. 'llm_client' - used for indexing. Can be slightly weaker model, as it will process entire codebase. It is using Groq API as an example, but can be local models as well.
2. query_client - this is the bot which will use tools and try to complete the task. I use a stronger model here.

Indexing:

```
python -m lucas.lcs index
```

Will produce file lucas.idx. It is a human-readable json file with summaries for files/directories


Querying:
```
python -m lucas.lcs query "What different LLM clients are used by this projects?"
```

Uses the tools and answers the question.

Making larger changes:
```
python -m lucas.lcs yolo "Let's log entire json conversation for each client implementation to a separate file. One call to send() should be logged to a separate temp file (persisted, not removed) and full name of this file should be written to normal log. Create a new class ConversationLogger which would handle this and used from every client."
```

Generates patches and applies them to automatically produce https://github.com/okuvshynov/lucas/commit/960369fd05788ed22d2db51d545be1997d687c9b



