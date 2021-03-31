# Requirements

- Python 3.7
- Rasa 1.10.20
- Django 3.1
- Jinja2 2.11.2
- Neo4j 4.1.1

# Running the conversational agent

Open a terminal window in the chatbot/Rasa folder and run
```
rasa train
```
to train the model, then execute
```
rasa run --enable-api
```
to start the rasa server.

Open another terminal window in the chatbot folder and run
```
python3.7 Rasa/actionserver.py
```
to start the action server.

Start the web server in a new terminal in the chatbot/chatbot_interface folder with:
```
python3.7 manage.py runserver
```

Now the chatbot is accessible under http://localhost:8000/ in your browser of choice.
