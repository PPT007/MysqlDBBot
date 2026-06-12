What problem does it solve?
 > Connects to mysql DB and then answers questions regarding the DB using natural language.

 The database is setup online, also the tables are seeded. (used antigravity to do so)

Language used: Python
The interface is vua terminal. 

Run .\venv\Scripts\Activate.ps1    to start venv  
Run main.py





This particular branch stores the embeddings in vector database. 
We store schema in text file and embeddings in json file as well, but just for logging. 
The data is retreived from database though for processing.