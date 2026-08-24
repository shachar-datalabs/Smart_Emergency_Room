# Local runtime

`docker-compose.yml` provides a single-node Kafka KRaft broker, idempotent topic
initialization and a Spark 3.5.5 execution container. Data and checkpoints are
bind-mounted beneath the ignored `data/` directory. No external database or
monitoring stack is required.
