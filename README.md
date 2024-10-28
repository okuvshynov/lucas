## Intro

In progress effort to experiment on efficient real-world software engineering tasks resolution.

```
lcs yolo "Let's log entire json conversation for each client implementation to a separate file. One call to send() should be logged to a separate temp file (persisted, not removed) and full name of this file should be written to normal log. Create a new class ConversationLogger which would handle this and used from every client."
```

Uses index, tools, generates patches and applies them to automatically produce https://github.com/okuvshynov/lucas/commit/960369fd05788ed22d2db51d545be1997d687c9b

Summary:
* Focus on making changes to medium-sized codebases, where change is spread across multiple files and project doesn't fit into the context;
* No autocomplete or generating snake game for 101st time.
* Human readable indexing with LLMs, which can be debugged and understood - no multidimensional vector stores.
* Focus on patch generation/application, not generating entire files from scratch to improve cost/latency.
* Support for local models (llama.cpp server) and remote LLM providers (claude, mistral, groq, cerebras).
* Support for version control tools (looking up commit info, blame, etc)

## First attempt at SWE-bench

Here's one single example `sqlfluff__sqlfluff-2419` from [swe-bench dev dataset](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Lite/viewer/default/dev?row=1). 

This project is big enough to not fit into context entirely, but index easily fits.

Sonnet 3.5 is used as 'main' model and locally running Llama 3.1 70B is used for indexing.

I ran it manually, indexing locally takes a while so I need to figure out better/faster way to do that (e.g. call some fast llama 70b API - cerebras or groq).

```
git clone https://github.com/sqlfluff/sqlfluff.git
cd sqlfluff
```

Switch to correct revision:
```
git checkout -b sqlfluff__sqlfluff-2419 f1dba0e1dd764ae72d67c3d5e1471cf14d3db030
```

create `lucas.conf` with content:

```
{
    "chunk_size": 4096,
    "llm_client": {"type": "LocalClient", "endpoint": "http://localhost:8080/v1/chat/completions", "max_req_size" : 65536},
    "query_client": {
        "type": "ClaudeClient",
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 8192,
        "tokens_rate": 200000,
        "cache": "ephemeral"
    },
    "crawler": {"includes": "*.py", "traverse": "git"},
    "token_counter" : {"type": "local_counter", "endpoint": "http://localhost:8080/tokenize"}
}
```


Run indexing, it took a few hours on M2 Utlra:

```

lcs index

```

Save the content of the query to `p2419.in` file:
```
Rule L060 could give a specific error message At the moment rule L060 flags something like this: ``` L: 21 | P: 9 | L060 | Use 'COALESCE' instead of 'IFNULL' or 'NVL'. ``` Since we likely know the wrong word, it might be nice to actually flag that instead of both `IFNULL` and `NVL` - like most of the other rules do. That is it should flag this: ``` L: 21 | P: 9 | L060 | Use 'COALESCE' instead of 'IFNULL'. ``` Or this: ``` L: 21 | P: 9 | L060 | Use 'COALESCE' instead of 'NVL'. ``` As appropriate. What do you think @jpy-git ?
```

Run lucas yolo to produce patch:

```
(base) studio ~/projects/sqlfluff % lcs yolof p2419.in
2024-10-26 08:42:28 INFO: {'directory': '/Users/oleksandr/projects/sqlfluff', 'message': "Rule L060 could give a specific error message At the moment rule L060 flags something like t
his: ``` L: 21 | P: 9 | L060 | Use 'COALESCE' instead of 'IFNULL' or 'NVL'. ``` Since we likely know the wrong word, it might be nice to actually flag that instead of both `IFNULL` a
nd `NVL` - like most of the other rules do. That is it should flag this: ``` L: 21 | P: 9 | L060 | Use 'COALESCE' instead of 'IFNULL'. ``` Or this: ``` L: 21 | P: 9 | L060 | Use 'COA
LESCE' instead of 'NVL'. ``` As appropriate. What do you think @jpy-git ?\n", 'index_file': '/Users/oleksandr/projects/sqlfluff/lucas.idx', 'client': {'type': 'ClaudeClient', 'model'
: 'claude-3-5-sonnet-20241022', 'max_tokens': 8192, 'tokens_rate': 200000, 'cache': 'ephemeral'}}
2024-10-26 08:42:28 INFO: loaded index
2024-10-26 08:42:28 INFO: sending payload, size = 19097
2024-10-26 08:42:33 INFO: Conversation logged to: /var/folders/qc/n9929lxs1hv_y70zclc7gpjh0000gn/T/lucas_claude_logs/claude_20241026_084233_383526.json
2024-10-26 08:42:33 INFO: Aggregate usage: {'input_tokens': 19, 'cache_creation_input_tokens': 21507, 'cache_read_input_tokens': 0, 'output_tokens': 53}
2024-10-26 08:42:33 INFO: input_tokens: 19, 0.00$ total
2024-10-26 08:42:33 INFO: cache_creation_input_tokens: 21507, 0.08$ total
2024-10-26 08:42:33 INFO: cache_read_input_tokens: 0, 0.00$ total
2024-10-26 08:42:33 INFO: output_tokens: 53, 0.00$ total
2024-10-26 08:42:33 INFO: requested tool: get_files({'filepaths': ['src/sqlfluff/rules/L060.py']})
2024-10-26 08:42:33 INFO: sending payload, size = 19740
2024-10-26 08:42:43 INFO: Conversation logged to: /var/folders/qc/n9929lxs1hv_y70zclc7gpjh0000gn/T/lucas_claude_logs/claude_20241026_084243_209730.json
2024-10-26 08:42:43 INFO: Aggregate usage: {'input_tokens': 671, 'cache_creation_input_tokens': 43028, 'cache_read_input_tokens': 0, 'output_tokens': 447}
2024-10-26 08:42:43 INFO: input_tokens: 671, 0.00$ total
2024-10-26 08:42:43 INFO: cache_creation_input_tokens: 43028, 0.16$ total
2024-10-26 08:42:43 INFO: cache_read_input_tokens: 0, 0.00$ total
2024-10-26 08:42:43 INFO: output_tokens: 447, 0.01$ total
2024-10-26 08:42:43 INFO: received final reply
2024-10-26 08:42:43 INFO: received 1 patches, applied 1.

```

We requested the right file from the start.
Note that we were not reusing claude cache here, it's because of  https://github.com/okuvshynov/lucas/blob/cd4064b7533fef19c9d7d462618e2332c8f1b442/lucas/clients/claude.py#L70-L75. We could cut down cost more if this is improved.

Check the patch:

```
(base) studio ~/projects/sqlfluff % git diff
diff --git a/src/sqlfluff/rules/L060.py b/src/sqlfluff/rules/L060.py
index 836941edc..5057f59a5 100644
--- a/src/sqlfluff/rules/L060.py
+++ b/src/sqlfluff/rules/L060.py
@@ -59,4 +59,6 @@ class Rule_L060(BaseRule):
             ],
         )

-        return LintResult(context.segment, [fix])
+        return LintResult(
+            context.segment, [fix],
+            description=f"Use 'COALESCE' instead of '{context.segment.raw}'.")
```

Looks good, but need to set up environment and implement faster indexing

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
