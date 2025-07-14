## Indexing
For prototyping, its fine to keep the data as a CSV file

Step 1: Generate documents from each row in the CSV file. Documents are the little slices of info that langchain uses to find which parts of your data are relavent to the question being asked
- Some information (i.e course name, credits) can be stored as metadata, meaning it doesn't get embedded but is still stored as relavent info. The only information that should get embedded is semantic info like course name and description




