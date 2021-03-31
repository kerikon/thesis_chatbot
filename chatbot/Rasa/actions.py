# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/core/actions/#custom-actions/

import jinja2
import datetime as dt
import time
from enum import Enum

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

from db_creator.src.Database import Database
from src.map_drawing import MapDraw


class Month(Enum):
    January = 1
    February = 2
    March = 3
    April = 4
    May = 5
    Juni = 6
    July = 7
    August = 8
    September = 9
    October = 10
    November = 11
    December = 12


class OrdinalNumber(Enum):
    first = 1
    second = 2
    third = 3
    fourth = 4
    fifth = 5
    sixth = 6
    seventh = 7
    eighth = 8
    ninth = 9
    tenth = 10
    eleventh = 11
    twelfth = 12
    thirteenth = 13
    fourteenth = 14
    fifteenth = 15
    sixteenth = 16
    seventeenth = 17
    eighteenth = 18
    nineteenth = 19
    twentieth = 20
    twentyfirst = 21
    twentysecond = 22
    twentythird = 23
    twentyfourth = 24
    twentyfifth = 25
    twentysixth = 26
    twentyseventh = 27
    twentyeighth = 28
    twentyninth = 29
    thirtieth = 30


def timestamp_to_string(timestamp):
    return time.strftime('%H:%M:%S', time.localtime(timestamp))


class ActionDefaultFallback(Action):

    def name(self) -> Text:
        return "action_default_fallback"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(template='utter_default')
        return []


class ActionSlotReset(Action):

    def name(self) -> Text:
        return "action_slot_reset"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return_slots = []
        for slot in tracker.slots:
            if slot != "selected_run":
                return_slots.append(SlotSet(slot, None))
        return return_slots


class ActionAllSlotReset(Action):

    def name(self) -> Text:
        return "action_all_slot_reset"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return_slots = []
        for slot in tracker.slots:
            return_slots.append(SlotSet(slot, None))
        return return_slots


class ActionGetRunAtDate(Action):

    def name(self) -> Text:
        return "action_get_run_at_date"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        db = Database('chatbot', 'chatbot')

        intent = tracker.latest_message['intent'].get('name')
        last_runs_from_slot = tracker.get_slot('last_runs')

        date_string = ""
        date = None

        if intent == 'run_at_date' or 'date_selection':
            for entity in tracker.latest_message['entities']:
                if entity['extractor'] == 'MSRTExtractor' and entity['entity'] == 'date':
                    date_string = entity['value']
            if date_string:
                date = dt.datetime.strptime(date_string, "%Y-%m-%d")

        output = ""
        last_runs = []

        if date:
            # Create jinja template loading environment
            template_loader = jinja2.FileSystemLoader('./jinja_templates/')
            template_env = jinja2.Environment(loader=template_loader)

            run_at_date_template = template_env.get_template("run_at_date_query.jinja")
            if last_runs_from_slot:
                query = run_at_date_template.render({'year': date.year,
                                                     'month': date.month,
                                                     'day': date.day,
                                                     'last_runs': True})

                result = db.read_query_with_list(query, last_runs_from_slot)
            else:
                query = run_at_date_template.render({'year': date.year,
                                                     'month': date.month,
                                                     'day': date.day})
                result = db.read_query(query)

            if result:
                if len(result) > 1:
                    output += f"Found {len(result)} runs"
                else:
                    output += f"Found {len(result)} run"
                output += f" on the {date.day}.{date.month}.{date.year}."
                output += " Choose the run you want to know more about"
                output += " by typing the number in the message input field:\n"
                run_counter = 1
                for node in result:
                    start_time = timestamp_to_string(node[0].get('start_time'))
                    end_time = timestamp_to_string(node[0].get('end_time'))
                    output += f"{run_counter}. Run, start time {start_time}, end time {end_time}.\n"
                    run_counter += 1
                    last_runs.append(node[0].get('bagfile_location'))
            else:
                output += f"No runs found at the {date.day}.{date.month}.{date.year}."
                output += " Should I display a calendar with dates, where runs were recorded?"
        else:
            output += "No date given to search runs at. Please type a date in the format dd.mm.yy."

        db.close()

        dispatcher.utter_message(text=output)

        return [SlotSet("last_runs", last_runs)]


class ActionListDatesForRuns(Action):

    def name(self) -> Text:
        return "action_list_dates_for_runs"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        output = ""
        date = ""
        date_split = ""

        db = Database('chatbot', 'chatbot')

        intent = tracker.latest_message['intent'].get('name')

        for entity in tracker.latest_message['entities']:
            if entity['extractor'] == 'MSRTExtractor' and entity['entity'] == 'daterange':
                date = entity['value']['start_date']

        # Create jinja template loading environment
        template_loader = jinja2.FileSystemLoader('./jinja_templates/')
        template_env = jinja2.Environment(loader=template_loader)

        dates_for_runs_template = template_env.get_template('get_dates_for_runs.jinja')

        if date:
            date_split = date.split('-')
            if intent == 'runs_in_month':
                query = dates_for_runs_template.render({'month': date_split[1]})
            elif intent == 'runs_in_year':
                query = dates_for_runs_template.render({'year': date_split[0]})
            else:
                query = dates_for_runs_template.render()
        else:
            query = dates_for_runs_template.render()

        result = db.read_query(query)

        last_runs = []
        dates = []

        if not result:
            if intent == 'runs_in_month':
                output += f"No runs found in the month of {Month(date_split[1]).name}."
                output += " Displaying all dates where data was recorded."
            elif intent == 'runs_in_year':
                output += f"No experiments found in the year {date_split[0]}."
                output += " Displaying all dates where data was recorded."
            query = dates_for_runs_template.render()
            result = db.read_query(query)

        if result:
            for date in result:
                date_string = dt.date(date[0].get('year'),
                                      date[1].get('month'),
                                      date[2].get('day')).strftime("%d.%m.%Y")
                dates.append(date_string)
                last_runs.extend(date[4])
            output += "Pick a date on the calendar or type a date in the message input field."
        else:
            output += "No runs found at all. Something is not right!"

        db.close()

        dispatcher.utter_message(text=output, json_message={'dates': dates})

        return [SlotSet("last_runs", last_runs)]


class ActionSelectRun(Action):

    def name(self) -> Text:
        return "action_select_run"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        selection = ""

        for entity in tracker.latest_message['entities']:
            if (entity['extractor'] == 'MSRTExtractor' and
                    (entity['entity'] == 'number' or entity['entity'] == 'ordinal')):
                selection = entity['value']

        output = ""
        selected_run = None
        runs = tracker.get_slot('last_runs')

        if selection and runs:
            if 1 <= int(selection) <= len(runs):
                selected_run = runs[int(selection) - 1]
                output = f"You have selected the {selection}. run. You can now ask questions about this run."
                output += " If you need information about a different run, please first ask for a topic"
                output += " or run change."
            else:
                output += f"Invalid number input, please select a run between 1 and {len(runs)}"

            dispatcher.utter_message(text=output)

            return [SlotSet("selected_run", selected_run)]
        else:
            output += "No runs found. Please first search for dates or runs before trying to select a"
            output += " specific run."

            dispatcher.utter_message(text=output)

            return []


class ActionFailureForRun(Action):

    def name(self) -> Text:
        return "action_failure_for_run"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        db = Database('chatbot', 'chatbot')

        output = ""

        selected_run = tracker.get_slot('selected_run')
        intent = tracker.latest_message['intent'].get('name')
        condition = None

        for entity in tracker.latest_message['entities']:
            if entity['entity'] == 'condition':
                condition = entity['value']

        if condition:
            if condition != "errors" and intent == "run_failure":
                condition = "errors"
            elif condition != "docking errors" and intent == "run_failure_docking":
                condition = "docking errors"
            elif condition != "navigation errors" and intent == "run_failure_navigation":
                condition = "navigation errors"
            elif condition != "automation errors" and intent == "run_failure_automation":
                condition = "automation errors"
            elif condition != "localization errors" and intent == "run_failure_localization":
                condition = "localization errors"
            elif condition != "no errors" and intent == "run_no_failure":
                condition = "no errors"

        if selected_run:
            # Create jinja template loading environment
            template_loader = jinja2.FileSystemLoader('./jinja_templates/')
            template_env = jinja2.Environment(loader=template_loader)

            failure_for_run_template = template_env.get_template("get_failure_for_run.jinja")

            query = failure_for_run_template.render({'selected_run': selected_run})

            result = db.read_query(query)

            if result:
                # 0 = run, 1 = actions, 2 = action_times, 3 = goal, 4 = exp
                # 5 = num_joypad_uses, 6 = goal_time, 7 = exp_time, 8 = cov_inc
                exp_failure = False
                goal_failure = False
                action_failure = False
                outside_help = False
                localization_failure = False
                failure_info = []
                exp = result[0][4]
                goal = result[0][3]
                actions = result[0][1]
                num_joypad_uses = result[0][5]
                cov_inc = result[0][8]
                if exp:
                    for e in exp:
                        if e.get('result') != "FINISHED":
                            exp_failure = True
                if goal:
                    for g in goal:
                        if g.get('status') != "SUCCEEDED":
                            goal_failure = True
                if actions:
                    failure_action_num = 0
                    for act in actions:
                        if 'state' in act:
                            if (act['state'] == "FAILED" or
                                    act['state'] == 'DOCKING_SEQUENCE_FAILED' or
                                    act['state'] == 'UNDOCKING_SEQUENCE_FAILED'):
                                action_failure = True
                                if failure_action_num > 0:
                                    failure_action_index = failure_action_num - 1
                                else:
                                    failure_action_index = 0
                                failure_info_dict = {'action': actions[failure_action_index],
                                                     'start_time': result[0][2][failure_action_index]['time'],
                                                     'end_time': result[0][2][failure_action_num]['time']}
                                if 'name' in act:
                                    failure_info_dict['procedure'] = act['name']
                                elif 'type' in act:
                                    failure_info_dict['procedure'] = act['type']

                                prev_action = actions[failure_action_index]

                                if 'action' in prev_action:
                                    failure_info_dict['action'] = prev_action['action']
                                elif 'type' in prev_action and 'state' in prev_action:
                                    failure_info_dict['action'] = prev_action['state']
                                else:
                                    failure_info_dict['action'] = 'UNAVAILABLE'
                                failure_info.append(failure_info_dict)
                        failure_action_num += 1

                if num_joypad_uses > 0:
                    outside_help = True

                if len(cov_inc) > 0:
                    localization_failure = True

                if condition == 'automation errors' and outside_help:
                    output += f"The joypad is used to give non-autonomous movement commands to the robot."
                    output += f" It was used {num_joypad_uses} times during this run."
                elif condition == 'automation errors' and not outside_help:
                    output += f"The joypad is used to give non-autonomous movement commands to the robot."
                    output += " It was not used during this run."
                elif condition == 'localization errors' and localization_failure:
                    output += f"The Covariance increased {len(cov_inc)} times"
                    output += " over a threshold of 0.5 during this run. Currently I can't give more information."
                elif condition == 'localization errors' and not localization_failure:
                    output += "There were no localization losses during this run."
                else:
                    if exp_failure or goal_failure or action_failure:
                        output += "This run reported"
                        if len(failure_info) == 1:
                            output += f" a failure during the '{failure_info[0]['procedure']}' procedure."
                            output += f" The error occured"
                            if failure_info[0]['action'] != 'UNAVAILABLE':
                                output += f" while performing the '{failure_info[0]['action']}' action"
                            output += f" at the following time {timestamp_to_string(failure_info[0]['start_time'])}"
                        elif len(failure_info) > 1:
                            output += f" {len(failure_info)} failures."
                            failure_counter = 1
                            for failure in failure_info:
                                output += f" The {OrdinalNumber(failure_counter).name} failure occured during the"
                                output += f" '{failure['procedure']}' procedure. The error occured"
                                if failure_info[0]['action'] != 'UNAVAILABLE':
                                    output += f" while performing the '{failure['action']}' action"
                                output += f" at the following time {timestamp_to_string(failure['start_time'])}"
                                failure_counter += 1
                        else:
                            output += " a failure. No further information is available"
                        output += "."
                    else:
                        output += "No failure occured during the execution of this run"
                        if outside_help:
                            output += f". But the robot needed help via joypad {num_joypad_uses} times"
                        if localization_failure:
                            output += f". and lost localization {len(cov_inc)} times during this run"
                        output += "."

        else:
            if condition and condition == 'no errors':
                output += f"There are multiple experiments without any errors. Should I display all of them in a calendar?"
            else:
                output += f"There are multiple experiments with {condition}. Should I display all of them in a calendar?"

        db.close()

        dispatcher.utter_message(text=output)

        return [SlotSet('condition', condition)]


class ActionSearchRunsWithCondition(Action):

    def name(self) -> Text:
        return "action_search_runs_with_condition"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        output = ""

        db = Database('chatbot', 'chatbot')

        condition = tracker.get_slot('condition')

        # Create jinja template loading environment
        template_loader = jinja2.FileSystemLoader('./jinja_templates/')
        template_env = jinja2.Environment(loader=template_loader)

        if (condition == 'errors'
                or condition == 'docking errors'
                or condition == 'navigation errors'
                or condition == 'automation errors'
                or condition == 'localization errors'):
            dates_for_runs_template = template_env.get_template('get_dates_for_runs_with_failures.jinja')
        elif condition == 'no errors':
            dates_for_runs_template = template_env.get_template('get_dates_for_runs_without_failures.jinja')
        else:
            dates_for_runs_template = template_env.get_template('get_dates_for_runs.jinja')

        query = dates_for_runs_template.render({'cond': condition})

        result = db.read_query(query)

        last_runs = []
        dates = []

        if result:
            for date in result:
                date_string = dt.date(date[0].get('year'),
                                      date[1].get('month'),
                                      date[2].get('day')).strftime("%d.%m.%Y")
                dates.append(date_string)
                last_runs.extend(date[4])
            output += f"Displaying all runs with {condition} on the calendar. Please pick a date"
            output += " or type a date in the message input field."
        else:
            output += f"No runs found with {condition}."

        db.close()

        dispatcher.utter_message(text=output, json_message={'dates': dates})

        return [SlotSet("last_runs", last_runs)]


class ActionDisplayPathForRun(Action):

    def name(self) -> Text:
        return "action_display_path_for_run"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        selected_run = tracker.get_slot('selected_run')
        intent = tracker.latest_message['intent'].get('name')

        db = Database('chatbot', 'chatbot')

        output = ""
        path_image_file_path = None

        if selected_run:
            # get poses of bot during run
            template_loader = jinja2.FileSystemLoader('./jinja_templates/')
            template_env = jinja2.Environment(loader=template_loader)

            poses_for_run_template = template_env.get_template('get_poses_for_run.jinja')

            query = poses_for_run_template.render({'selected_run': selected_run})

            result = db.read_query(query)

            if len(result) > 1:
                path_image_file_path = MapDraw.draw_path(result, 800, 'b')

                output += "The blue arrows show the path the ROPOD took during this experiment."
                output += " You can click on the image to enlarge it."
            elif len(result) == 1:
                path_image_file_path = MapDraw.draw_position(result[0][1], 800)

                output += f"The picture shows the position of the ROPOD. You can click on the image to enlarge it."
            else:
                output += "Sorry, I could not find any path data for this run."
        else:
            output += "There are multiple recorded experiments. You have to first select an experiment"
            if intent == 'run_position_at_time':
                output += " to view the position. Should I list dates, where experiment data was recorded?"
            else:
                output += " to view the traveled path. Should I list dates, where experiment data was recorded?"

        db.close()

        dispatcher.utter_message(text=output, image=path_image_file_path)

        return []


class ActionDisplayPositionAtTimeForRun(Action):

    def name(self) -> Text:
        return "action_display_position_at_time_for_run"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        selected_run = tracker.get_slot('selected_run')
        last_asked_time = tracker.get_slot('last_asked_time')

        db = Database('chatbot', 'chatbot')

        output = ""
        path_image_file_path = None
        timestamp = None

        for entity in tracker.latest_message['entities']:
            if entity['extractor'] == 'MSRTExtractor' and entity['entity'] == 'time':
                timestamp = entity['value']

        if selected_run:
            # get poses of bot during run
            template_loader = jinja2.FileSystemLoader('./jinja_templates/')
            template_env = jinja2.Environment(loader=template_loader)

            poses_for_run_template = template_env.get_template('get_poses_for_run.jinja')

            result = None

            if timestamp:
                query = poses_for_run_template.render({'selected_run': selected_run,
                                                       'timestamp': timestamp})
                result = db.read_query(query)
            elif last_asked_time:
                query = poses_for_run_template.render({'selected_run': selected_run,
                                                       'timestamp': last_asked_time})
                result = db.read_query(query)

            if result:
                path_image_file_path = MapDraw.draw_position(result[0][1], 800)

                output += f"The picture shows the position of the ROPOD at {timestamp} o'clock."
                output += " Clicking on the image enlarges it."
            else:
                if timestamp:
                    output += f"Sorry, I could not find any position data at {timestamp} o'clock for this run."
                else:
                    output += "Sorry, I could not extract a time value from your message. Please specify time in this"
                    output += " format: HH:MM:SS"
        else:
            output += "There are multiple recorded experiments. You have to first select an experiment"
            output += " to view the position. Should I list dates, where experiment data was recorded?"

        db.close()

        dispatcher.utter_message(text=output, image=path_image_file_path)

        return [SlotSet("last_asked_time", timestamp)]


class ActionGoalOrExpStatus(Action):

    def name(self) -> Text:
        return "action_goal_or_exp_status"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        db = Database('chatbot', 'chatbot')

        last_rel_intent = tracker.latest_message['intent'].get('name')

        selected_run = tracker.get_slot('selected_run')

        if last_rel_intent != 'goal_status' and last_rel_intent != 'exp_status':
            last_rel_intent = tracker.get_slot('last_rel_intent')
            if not last_rel_intent:
                last_rel_intent = 'exp_status'

        output = ""

        if selected_run:
            template_loader = jinja2.FileSystemLoader('./jinja_templates/')
            template_env = jinja2.Environment(loader=template_loader)

            status_template = template_env.get_template('get_goal_or_exp_status.jinja')

            query = status_template.render({'selected_run': selected_run,
                                            'intent': last_rel_intent})
            result = db.read_query(query)

            if result:
                if last_rel_intent == 'goal_status':
                    if len(result) > 1:
                        output += f"This run has {len(result)} goals.\n"
                        index = 1
                        for res in result:
                            goal_type = res[2]
                            goal_status = res[1]
                            load_id = res[3]
                            output += f"The {OrdinalNumber(index).name} goal"
                            if goal_type:
                                output += f" is of type \"{goal_type}\"."
                            else:
                                output += "\'s type is unknown."
                            if goal_status == 'SUCCEEDED':
                                output += " It completed successfully"
                                if load_id:
                                    if goal_type == 'DOCK':
                                        output += f" and docked onto \"{load_id}\""
                                    else:
                                        output += f" and undocked from \"{load_id}\""
                                output += ".\n"
                            else:
                                output += " It was aborted.\n"
                            index += 1
                    else:
                        goal_type = result[0][2]
                        goal_status = result[0][1]
                        load_id = result[0][3]

                        output += f"This run has one goal, which"
                        if goal_type:
                            output += f" is of type \"{goal_type}\"."
                        else:
                            output += "\' type is unknown."
                        if goal_status == 'SUCCEEDED':
                            output += " It completed successfully"
                            if load_id:
                                if goal_type == 'DOCK':
                                    output += f" and docked onto \"{load_id}\""
                                else:
                                    output += f" and undocked from \"{load_id}\""
                            output += ".\n"
                        else:
                            output += " It was aborted.\n"
                else:
                    if len(result) > 1:
                        output += f"This run has {len(result)} experiments.\n"
                        index = 1
                        for res in result:
                            exp_type = res[2]
                            exp_status = res[1]
                            exp_result = res[3]
                            output += f"The {OrdinalNumber(index).name} experiment"
                            if exp_type:
                                output += f" is of type \"{exp_type}\"."
                            else:
                                output += "\'s type is unknown."
                            if exp_status == 'SUCCEEDED':
                                if exp_result == 'FINISHED':
                                    output += " It completed successfully.\n"
                                else:
                                    output += " It failed.\n"
                            else:
                                output += " It was aborted.\n"
                            index += 1
                    else:
                        exp_type = result[0][2]
                        exp_status = result[0][1]
                        exp_result = result[0][3]

                        output += f"This run has one experiment, which"
                        if exp_type:
                            output += f" is of type \"{exp_type}\"."
                        else:
                            output += "\' type is unknown."
                        if exp_status == 'SUCCEEDED':
                            if exp_result == 'FINISHED':
                                output += " It completed successfully.\n"
                            else:
                                output += " It failed.\n"
                        else:
                            output += " It was aborted.\n"
        else:
            output += "There are multiple recorded experiments. You have to first select an experiment"
            if last_rel_intent == 'goal_status':
                output += " to view the goal status."
            else:
                output += " to view the experiment status."
            output += " Should I display dates, where data was recorded?"

        db.close()

        dispatcher.utter_message(text=output)

        return [SlotSet("last_rel_intent", last_rel_intent)]


class ActionGetActionAtTime(Action):
    def name(self) -> Text:
        return "action_get_action_at_time"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        db = Database('chatbot', 'chatbot')

        selected_run = tracker.get_slot('selected_run')

        last_asked_time = tracker.get_slot('last_asked_time')

        timestamp = None

        for entity in tracker.latest_message['entities']:
            if entity['extractor'] == 'MSRTExtractor' and entity['entity'] == 'time':
                timestamp = entity['value']

        output = ""

        if selected_run:
            if timestamp or last_asked_time:
                template_loader = jinja2.FileSystemLoader('./jinja_templates/')
                template_env = jinja2.Environment(loader=template_loader)

                goal_status_template = template_env.get_template('get_actions_for_run.jinja')

                query = goal_status_template.render({'selected_run': selected_run})
                result = db.read_query(query)

                if result:
                    year = result[0][0].get('year')
                    month = result[0][1].get('month')
                    day = result[0][2].get('day')
                    nodes = result[0][4]
                    rel = result[0][5]

                    if timestamp:
                        search_time = dt.datetime.strptime(f"+0200-{year}-{month}-{day}-" + timestamp,
                                                           "%z-%Y-%m-%d-%H:%M:%S")
                    else:
                        search_time = dt.datetime.strptime(f"+0200-{year}-{month}-{day}-" + last_asked_time,
                                                           "%z-%Y-%m-%d-%H:%M:%S")
                    tz = dt.timezone(dt.timedelta(hours=2))

                    actions_and_times = []
                    for i, e in enumerate(rel):
                        time_as_datetime = dt.datetime.fromtimestamp(e.get('time'), tz=tz)
                        # check for exact time match
                        if time_as_datetime == search_time:
                            if i == 0:
                                actions_and_times.append({'index': i + 1,
                                                          'start_time': dt.datetime.fromtimestamp(e.get('time'),
                                                                                                  tz=tz),
                                                          'end_time': dt.datetime.fromtimestamp(rel[i + 1].get('time'),
                                                                                                tz=tz),
                                                          'action': nodes[i + 1]})
                            else:
                                if actions_and_times and actions_and_times[0]['index'] == i:
                                    continue
                                else:
                                    actions_and_times.append({'index': i,
                                                              'start_time': dt.datetime.fromtimestamp(
                                                                  rel[i - 1].get('time'),
                                                                  tz=tz),
                                                              'end_time': dt.datetime.fromtimestamp(e.get('time'),
                                                                                                    tz=tz),
                                                              'action': nodes[i]})
                        # if there is no exact match, check for greater match, take only first greater match
                        elif time_as_datetime > search_time and not actions_and_times:
                            if i == 0:
                                actions_and_times.append({'index': i + 1,
                                                          'start_time': dt.datetime.fromtimestamp(e.get('time'),
                                                                                                  tz=tz),
                                                          'end_time': dt.datetime.fromtimestamp(rel[i + 1].get('time'),
                                                                                                tz=tz),
                                                          'action': nodes[i + 1]})
                            else:
                                actions_and_times.append({'index': i,
                                                          'start_time': dt.datetime.fromtimestamp(rel[i-1].get('time'),
                                                                                                  tz=tz),
                                                          'end_time': dt.datetime.fromtimestamp(e.get('time'),
                                                                                                tz=tz),
                                                          'action': nodes[i]})

                    if actions_and_times and len(actions_and_times) > 1:
                        output += f"The ROPOD performed {len(actions_and_times)} actions"
                        output += f" at {search_time.strftime('%H:%M:%S')}:\n"
                        i = 1
                        for act in actions_and_times:
                            if act['action'].get('name'):
                                output += f"{i}. {act['action'].get('name')} from"
                                output += f" {act['start_time'].strftime('%H:%M:%S')}"
                                output += f" to {act['end_time'].strftime('%H:%M:%S')}\n"
                            elif act['action'].get('action'):
                                output += f"{i}. {act['action'].get('action')} from"
                                output += f" {act['start_time'].strftime('%H:%M:%S')}"
                                output += f" to {act['end_time'].strftime('%H:%M:%S')}\n"
                            else:
                                output += f"{i}. {act['action'].get('state')} from"
                                output += f" {act['start_time'].strftime('%H:%M:%S')}"
                                output += f" to {act['end_time'].strftime('%H:%M:%S')}\n"
                            i += 1
                    elif actions_and_times:
                        if actions_and_times[0]['action'].get('name'):
                            act = actions_and_times[0]['action'].get('name')
                        elif actions_and_times[0]['action'].get('action'):
                            act = actions_and_times[0]['action'].get('action')
                        else:
                            act = actions_and_times[0]['action'].get('state')
                        output += f"The ROPOD performed the {act} action from"
                        output += f" {actions_and_times[0]['start_time'].strftime('%H:%M:%S')}"
                        output += f" to {actions_and_times[0]['end_time'].strftime('%H:%M:%S')} o'clock.\n"
                    else:
                        output += f"No performed actions found at {search_time.strftime('%H:%M:%S')} o'clock.\n"
            else:
                output += "No time given. Please give a time with the format hh:mm:ss."
        else:
            output += "There are multiple recorded experiments. You have to first select an experiment"
            output += " to view the action performed. Should I display dates, where experiment data was recorded?"

        db.close()

        dispatcher.utter_message(text=output)

        return [SlotSet("last_asked_time", timestamp)]


class ActionGetNumRunsRecorded(Action):
    def name(self) -> Text:
        return "action_get_num_runs_recorded"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        db = Database('chatbot', 'chatbot')

        date = None
        date_split = None
        is_full_date = False
        is_month_date = False

        for entity in tracker.latest_message['entities']:
            if entity['extractor'] == 'MSRTExtractor' and entity['entity'] == 'date':
                date = entity['value']
                is_full_date = True
            elif entity['extractor'] == 'MSRTExtractor' and entity['entity'] == 'daterange':
                date = entity['value']['start_date']
                start_date = dt.datetime.strptime(entity['value']['start_date'], "%Y-%m-%d")
                end_date = dt.datetime.strptime(entity['value']['end_date'], "%Y-%m-%d")
                if 25 <= (end_date - start_date).days <= 360:
                    is_month_date = True

        output = ""

        template_loader = jinja2.FileSystemLoader('./jinja_templates/')
        template_env = jinja2.Environment(loader=template_loader)

        num_runs_template = template_env.get_template('num_runs_recorded.jinja')

        if date:
            date_split = date.split('-')
            if is_full_date:
                query = num_runs_template.render({'year': date_split[0],
                                                  'month': date_split[1],
                                                  'day': date_split[2]})
            elif is_month_date:
                query = num_runs_template.render({'month': date_split[1],
                                                  'year': date_split[0]})
            else:
                query = num_runs_template.render({'year': date_split[0]})
        else:
            query = num_runs_template.render()

        result = db.read_query(query)

        if result:
            if result[0][0] == 1:
                output += f"There is {result[0][0]} experiment recorded"
            else:
                output += f"There are {result[0][0]} experiments recorded"
            if date_split:
                if is_full_date:
                    output += f" at {date_split[2]}.{date_split[1]}.{date_split[0]}."
                elif is_month_date:
                    output += f" in {Month(int(date_split[1])).name} {date_split[0]}."
                else:
                    output += f" in {date_split[0]}."
            else:
                output += " overall."
        else:
            output += "The search for number of runs failed."

        db.close()

        dispatcher.utter_message(text=output)

        return []


class ActionSelectedRunInfo(Action):
    def name(self) -> Text:
        return "action_selected_run_info"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        db = Database('chatbot', 'chatbot')

        selected_run = tracker.get_slot('selected_run')

        output = ""

        if selected_run:
            template_loader = jinja2.FileSystemLoader('./jinja_templates/')
            template_env = jinja2.Environment(loader=template_loader)

            run_at_date_template = template_env.get_template("run_at_date_query.jinja")

            query = run_at_date_template.render({'selected_run': selected_run})

            result = db.read_query(query)

            if result:
                start_time = timestamp_to_string(result[0][0].get('start_time'))
                end_time = timestamp_to_string(result[0][0].get('end_time'))
                output += "Your currently selected run was executed at"
                output += f" {result[0][3].get('day')}.{result[0][2].get('month')}.{result[0][1].get('year')}."
                output += f" The run started at {start_time} and ended at {end_time}."
            else:
                output += "Could not find selected run."
        else:
            output += "You have no run selected currently."

        db.close()

        dispatcher.utter_message(text=output)

        return []

# /media/bagfiles/Ragith/2020_04_01/20200401_cart_transportation_hs.bag
