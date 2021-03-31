import datetime

from django.shortcuts import render

from .chatbot_access import Chatbot

chatbot = Chatbot()


def index(request):
    global chatbot

    response = []
    user_input = ""

    if request.GET.get('datepicker'):
        user_input = request.GET.get('datepicker')
        response = request.session['response']

    if request.GET.get('input'):
        user_input = request.GET.get('input')

        input_message = {'message': user_input,
                         'time': datetime.datetime.now().strftime("%d. %b | %H:%M"),
                         'sender': 'user',
                         'type': 'text'}

        response = request.session['response']

        response.append(input_message)

    text_responses, image_responses, dates_responses = chatbot.get_response(user_input)

    for chatbot_response in image_responses:
        if chatbot_response:
            message = {'message': chatbot_response,
                       'sender': 'chatbot',
                       'type': 'image'}
            response.append(message)

    for date_response in dates_responses:
        message = {'message': date_response,
                   'sender': 'chatbot',
                   'type': 'date',
                   'id': len(response)}
        response.append(message)

    for chatbot_response in text_responses:
        message = {'message': chatbot_response,
                   'time': datetime.datetime.now().strftime("%d. %b | %H:%M"),
                   'sender': 'chatbot',
                   'type': 'text'}
        response.append(message)

    request.session['response'] = response

    context = {'title': 'Chatbot Version 1.0', 'response': response}

    return render(request, 'Chatbot/index.html', context)
