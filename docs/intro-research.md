intro research

so basically were making a note saving app with a browser extension and semantic search. target audience is students

the problem is that apps like notion and evernote make you go to their site every time you wanna save something which is annoying. and then when you try to find stuff later the search only does exact keyword matching so if you dont remember exactly what you wrote youre screwed

features:
- upload docs
- chrome extension for one click saving
- semantic search
- graph view for connections between notes
- basic note editor
- folders
- voice memo to text (if we have time)

stack:
- chrome ext: js + react, no choice here chrome forces you to use js. react bc we already know it
- frontend: node + shadcn
- backend: python fastapi
- ml: pytorch, huggingface
- db: supabase + cloudflare vectorize
- voice: aws transcribe


VECTORIZATION RESEARCH

looked into embedding models today

sentence transformers (huggingface)
- free and runs locally which is nice
- tried all-MiniLM-L6-v2, its fast and pretty accurate for how small it is
- docs are decent, lots of examples online
- gonna go with this one probably

openai embeddings
- super easy to set up, like 3 lines of code
- but costs money per request which adds up fast
- dont love relying on external api either, what if it goes down
- pass

cohere
- similar deal to openai, easy but $$$
- their playground is cool for testing tho
- still probably not worth it for us

for chunking i watched some youtube videos and read a medium article. most ppl do like 512 tokens with some overlap so you dont cut off sentences weird. gonna have to test this more

cosine similarity for matching, still need to figure out good threshold


GRAPH VIZ

looked at 3 libraries

d3.js
- super powerful you can do basically anything
- but the learning curve is insane, spent an hour and barely got a circle on screen
- overkill for what we need
- not using

vis.js
- way simpler to get started
- made a basic node graph in like 20 min
- docs are ok not great but theres enough stackoverflow answers
- this is probably what well use

cytoscape.js
- specifically made for graphs which is cool
- more features than vis.js
- but also more complex
- might switch to this later if vis.js cant do something we need


BROWSER EXTENSION

tested mozilla readability for content extraction
- works surprisingly well, strips out all the garbage (ads, nav, footers)
- easy to plug in
- only issue is it doesnt work great on some sites that load content dynamically
- good enough for now

also looked at cheerio for scraping but readability is cleaner for our use case


VOICE STUFF

aws transcribe
- accurate, handles most audio formats
- pricing is reasonable
- kinda annoying to set up with all the aws config stuff
- might need ffmpeg to convert some formats first

also saw whisper from openai
- can run locally which is cool
- but probably slower and more work to set up
- sticking with transcribe for now


RISKS
- vectorization too hard - just use off the shelf model
- ml doesnt work well - throw more ppl at it
- too much scope - cut features

next: test embeddings more, figure out db schema, make figma mocks, setup ci
