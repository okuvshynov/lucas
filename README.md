## Intro

In progress effort to experiment on efficient real-world software engineering tasks resolution.

```
lcs yolo "Let's log entire json conversation for each client implementation to a separate file. One call to send() should be logged to a separate temp file (persisted, not removed) and full name of this file should be written to normal log. Create a new class ConversationLogger which would handle this and used from every client."
```

Uses index, tools, generates patches and applies them to automatically produce https://github.com/okuvshynov/lucas/commit/960369fd05788ed22d2db51d545be1997d687c9b

Summary:
* Focus on making changes to medium-sized codebases, where change is spread across multiple files and project doesn't fit into the context;
* No autocomplete or generating snake game for 101th time.
* Human readable indexing with LLMs, which can be debugged and understood - no multidimensional vector stores.
* Focus on patch generation/application, not generating entire files from scratch to improve cost/latency.
* Support for local models (llama.cpp server) and remote LLM providers (claude, mistral, groq, cerebras).
* Support for version control tools (looking up commit info, blame, etc)

## Next experiments

* Automated tool generation: https://github.com/okuvshynov/lucas/blob/main/lucas/prompts/auto_tools.txt, https://github.com/okuvshynov/lucas/commit/95f43206e36b5cf9a281f3f08881b9a9a5e3e876 - something similar to CoT but let it produce tools first. Chain could look like a) decide which tools are needed b) implement tools c) use tools. With more intermediate steps for testing.
* Experiment on larger projects and add tools for index exploration.
* test it on swe bench
* * batch processing for local indexing to speed it up


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
1. llm_client - used for indexing. Can be slightly weaker model, as it will process entire codebase. It is using Groq API as an example, but can be local models as well.
2. query_client - this is the bot which will use tools and try to complete the task. I use a stronger model here.

Install locally:

```
pip install -e .
```

### Commands

#### Indexing

```
lcs index
```

Will produce file lucas.idx. It is a human-readable json file with summaries for files/directories. If file already exists, lcs will check if any files are new/changed/deleted and redo the changed files + parent directories.


#### Querying

```
lcs query "What different LLM clients are used by this projects?"
```

Uses index, tools and answers the question.



### Getiing index stats

```
lcs stat
```
Shows size of the index (files, dirs, tokens).
