# Advanced Cases

## Spider

*See `examples/advanced/spider.json`.*

Files on a server are splited into shards:
```
shard.en.01.txt, shard.en.02.txt, shard.en.03.txt, ...
shard.de.01.txt, shard.de.02.txt, shard.de.03.txt, ...
```

We want to download it to:
```
Downloads/en.01, ...
```

Run it with the `latency` argument (sleep `x` seconds before running a new task) to avoid being blacklisted by the server.

```bash
manytasks run spider --latency 3
```

## Everything

*See `examples/advanced/everything.json`.*

This configuration tells almost every feature of `manytasks` (which I do not have time to write a friendly and detailed document), try it!

```bash
manytasks run everything
```
