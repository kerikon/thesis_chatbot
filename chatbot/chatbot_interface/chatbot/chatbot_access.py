import requests
from requests.exceptions import HTTPError, Timeout

import logging
import logging.handlers
import time


class Chatbot(object):
    """Provides access to Rasa"""

    def __init__(self):

        # Initialize logging
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

        log_file_name = time.strftime("chatbot/logs/%d.%m.%Y_%H_%M_%S_conversation.log")

        file_handler = logging.handlers.RotatingFileHandler(log_file_name, mode="w")
        file_handler.setLevel(logging.INFO)

        self.logger.addHandler(file_handler)

    def get_response(self, user_input=''):
        text_responses = []
        image_responses = []
        dates_response = []

        responses_json = ""

        if user_input:
            self.logger.info(f"[{time.strftime('%H:%M:%S', time.localtime())}] User: {user_input}\n")

            json_string = "{\"sender\":\"User\",\"message\":\"" + user_input + "\"}"

            try:
                responses = requests.post('http://localhost:5005/webhooks/rest/webhook', data=json_string)

                # If the response was successful, no Exception will be raised
                responses.raise_for_status()
            except HTTPError as http_err:
                print(f'HTTP error occurred: {http_err}')
                return http_err
            except Timeout as timeout_err:
                print(f'Rasa Server not running!')
                return timeout_err
            except Exception as err:
                print(f'Other error occurred: {err}')
                return err

            responses_json = responses.json()

        if responses_json:
            for response in responses_json:
                if 'text' in response:
                    text_responses.append(response['text'])
                    self.logger.info(f"[{time.strftime('%H:%M:%S', time.localtime())}] Bot: {response['text']}\n")
                if 'image' in response:
                    image_responses.append(response['image'])
                    self.logger.info(f"[{time.strftime('%H:%M:%S', time.localtime())}] "
                                     f"Bot: Image Location - {response['image']}\n")
                if 'custom' in response:
                    dates_response.append(response['custom']['dates'])
                    self.logger.info(f"[{time.strftime('%H:%M:%S', time.localtime())}] "
                                     f"Bot: Dates to display - {str(response['custom']['dates'])}\n")
        else:
            default_response = "Greetings, I am the robot used in the ROPOD project."
            default_response += " You can ask me about when I collected data, errors during runs, traveled paths,"
            default_response += " fullfilled goals and more. About what do you want to know more?"
            text_responses.append(default_response)
            self.logger.info(f"[{time.strftime('%H:%M:%S', time.localtime())}] Bot: {default_response}\n")

        return text_responses, image_responses, dates_response
