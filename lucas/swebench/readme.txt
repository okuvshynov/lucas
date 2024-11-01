Example run:

1. Run one specific task:
python -m lucas.swebench.swebench sqlfluff__sqlfluff-2419

2. Validate:

python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Lite \
    --predictions_path /tmp/lucas_swebench/sqlfluff__sqlfluff-2419_patch.json \
    --max_workers 4 \
    --run_id 1 --split dev

Interesting:
    * https://www.anthropic.com/research/swe-bench-sonnet

What should we do? 
[ ] Go one by one and check how we could resolve it
[ ] Indexing with haiku 3.5
[ ] Understand patch application - is just replacing better than producing patches -- seems so.
[ ] Indexing git history
[ ] Tool exploration - ask agent to build a tool it needs.
[ ] debugger tool. Ask to reproduce the bug, then put a tracepoint and iterate.
