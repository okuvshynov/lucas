example queries to be used with lucas service.

curl -X POST -H "Content-Type: application/json" -d @lucas/queries/extract_rate_limiting_query.json http://127.0.0.1:5000/yolo

curl -X POST -H "Content-Type: application/json" -d @lucas_conf.json http://127.0.0.1:5000/jobs
