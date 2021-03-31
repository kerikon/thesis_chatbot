## greetings
* greet
  - utter_greet
  
* general_capabilities OR about_you OR number_selection OR date_selection
  - utter_information_available
  
## What else
* affirm
  - utter_what_else
    
## say goodbye
* goodbye
  - utter_goodbye
  - action_all_slot_reset
  
## positive feedback
* positive_feedback
  - utter_thanks
  
## topic change
* topic_change
  - utter_topic_change
  - action_all_slot_reset
    
## bot challenge
* bot_challenge
  - utter_iamabot
    
## get runs at specific date, runs found, selected run, what info available
* run_at_date{"date": ""}
  - action_get_run_at_date
* number_selection{"number": ""} OR date_selection{"date": ""}
  - action_select_run
  - action_slot_reset
* general_capabilities
  - utter_information_available
    
## get runs at specific date, no runs found, accept list
* run_at_date{"date": ""}
  - action_get_run_at_date
* affirm OR positive_feedback
  - action_list_dates_for_runs
* date_selection{"date": ""}
  - action_get_run_at_date
* number_selection{"number": ""} OR date_selection{"date": ""}
  - action_select_run
  - action_slot_reset
  
## get runs at a specific date, no runs found, deny list
* run_at_date{"date": ""}
  - action_get_run_at_date
* deny OR negative_feedback OR topic_change
  - utter_topic_change
  - action_all_slot_reset
  
## get runs at a specific month or year
* runs_in_month{"daterange": ""} OR runs_in_year{"daterange": ""}
  - action_list_dates_for_runs
* date_selection{"date": ""} OR number_selection{"number": ""}
  - action_get_run_at_date
* number_selection{"number": ""} OR date_selection{"date": ""}
  - action_select_run
  - action_slot_reset
  
## get runs at a specific month or year, deny list
* runs_in_month{"daterange": ""} OR runs_in_year{"daterange": ""}
  - action_list_dates_for_runs
* deny OR negative_feedback OR topic_change
  - utter_topic_change
  - action_all_slot_reset
  
## get all runs, positive
* list_all_runs
  - action_list_dates_for_runs
* date_selection{"date": ""} OR number_selection{"number": ""}
  - action_get_run_at_date
* number_selection{"number": ""} OR date_selection{"date": ""}
  - action_select_run
  - action_slot_reset  
  
## get all runs, negative
* list_all_runs
  - action_list_dates_for_runs
* deny OR negative_feedback OR topic_change
  - utter_topic_change
  - action_all_slot_reset
  
## failure question with selected run
* run_failure{"condition": "errors"} OR run_failure_navigation{"condition": "navigation errors"} OR run_failure_docking{"condition": "docking errors"} OR run_failure_automation{"condition": "automation errors"} OR run_failure_localization{"condition": "localization errors"} OR run_no_failure{"condition": "no errors"}
  - action_failure_for_run
  
## failure question, happy search
* run_failure{"condition": "errors"} OR run_failure_navigation{"condition": "navigation errors"} OR run_failure_docking{"condition": "docking errors"} OR run_failure_automation{"condition": "automation errors"} OR run_failure_localization{"condition": "localization errors"} OR run_no_failure{"condition": "no errors"}
  - action_failure_for_run
* affirm OR positive_feedback
  - action_search_runs_with_condition
* date_selection{"date": ""} OR number_selection{"number": ""}
  - action_get_run_at_date
* number_selection{"number": ""} OR date_selection{"date": ""}
  - action_select_run
  - action_failure_for_run
  - action_slot_reset
  
## failure question, sad search
* run_failure{"condition": "errors"} OR run_failure_navigation{"condition": "navigation errors"} OR run_failure_docking{"condition": "docking errors"} OR run_failure_automation{"condition": "automation errors"} OR run_failure_localization{"condition": "localization errors"} OR run_no_failure{"condition": "no errors"}
  - action_failure_for_run
* deny OR negative_feedback OR topic_change
  - utter_topic_change
  - action_all_slot_reset
  
## path, selected run
* run_path{"path": ""}
  - action_display_path_for_run
  
## path, no selected run
* run_path{"path": ""}
  - action_display_path_for_run
* affirm OR positive_feedback
  - action_list_dates_for_runs
* date_selection{"date": ""} OR number_selection{"number": ""}
  - action_get_run_at_date
* number_selection{"number": ""} OR date_selection{"date": ""}
  - action_select_run
  - action_display_path_for_run
  - action_slot_reset
  
## path, search not wanted
* run_path{"path": ""}
  - action_display_path_for_run
* deny OR negative_feedback OR topic_change
  - utter_topic_change
  - action_all_slot_reset
  
## Position at time, selected run
* run_position_at_time{"time": ""}
  - action_display_position_at_time_for_run
  
## Position at time, no selected run
* run_position_at_time{"time": ""}
  - action_display_position_at_time_for_run
* affirm OR positive_feedback
  - action_list_dates_for_runs
* date_selection{"date": ""} OR number_selection{"number": ""}
  - action_get_run_at_date
* number_selection{"number": ""} OR date_selection{"date": ""}
  - action_select_run
  - action_display_position_at_time_for_run
  - action_slot_reset
  
## Position at time, search not wanted
* run_position_at_time{"time": ""}
  - action_display_position_at_time_for_run
* deny OR negative_feedback OR topic_change
  - utter_topic_change
  - action_all_slot_reset
  
## Get goal or experiment status
* goal_status{"condition": "goal"} OR exp_status{"condition": "experiment"}
  - action_goal_or_exp_status
  
## Get goal or experiment status, no selected run
* goal_status{"condition": "goal"} OR exp_status{"condition": "experiment"}
  - action_goal_or_exp_status
* affirm OR positive_feedback
  - action_list_dates_for_runs
* date_selection{"date": ""} OR number_selection{"number": ""}
  - action_get_run_at_date
* number_selection{"number": ""} OR date_selection{"date": ""}
  - action_select_run
  - action_goal_or_exp_status
  - action_slot_reset
  
## Get goal or experiment status, search not wanted
* goal_status{"condition": "goal"} OR exp_status{"condition": "experiment"}
  - action_goal_or_exp_status
* deny OR negative_feedback OR topic_change
  - utter_topic_change
  - action_all_slot_reset
  
## Get the action at timestamp
* action_at_time{"time": ""}
  - action_get_action_at_time
  
## Position at time, no selected run
* action_at_time{"time": ""}
  - action_get_action_at_time
* affirm OR positive_feedback
  - action_list_dates_for_runs
* date_selection{"date": ""} OR number_selection{"number": ""}
  - action_get_run_at_date
* number_selection{"number": ""} OR date_selection{"date": ""}
  - action_select_run
  - action_get_action_at_time
  - action_slot_reset
  
## Num runs
* num_runs_recorded
  - action_get_num_runs_recorded
  
## Information about the currently selected run
* info_selected_run
  - action_selected_run_info