**Duplicate embeddings are cretaed in the vector db everytime I generate a new schema**
-  replace insert with upsert

-------------

**Use caching to improve response time and reduce llm calls**
- store user question embedding along with generated sql query in db
- compare the next question embeddding with db embeddings, if the match is more than 98%, return the query associated with that embedding.
- mantain a "last used" column, update it when the embedding matches. Allpw only 1000 cache entries. Find which is the least recently used (LRU strategy) and clear those cache entries if u hit 1000 entries.
- when new schema is generated, clear the cache table.


