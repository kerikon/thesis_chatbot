import os
import time

import rosbag
import yaml
import jinja2
import numpy as np
import matplotlib.pyplot as plt

from db_creator.src.Database import Database
from db_creator.src.OSMHandler import OSMHandler
from db_creator.src.Status import Status, FeedbackStatus

from PIL import Image, ImageOps


def time_to_string(time_in_sec):
    return time.strftime('%H_%M_%S', time.localtime(time_in_sec))


def get_file_names(directory):
    files_list = []
    if os.path.isdir(directory):
        for path, subdirs, files in os.walk(directory):
            for name in files:
                files_list.append(os.path.join(path, name))
        return files_list
    else:
        print('Could not find bag file directory!')
        exit(1)


def calculate_avg_max_speed(velocities):
    average = {'linear': 0, 'angular': 0}
    maximum = {'linear': 0, 'angular': 0}

    if len(velocities) > 0:
        average['linear'] = sum(abs(vel['lin_x']) for vel in velocities) / len(velocities)
        average['angular'] = sum(abs(vel['ang_z']) for vel in velocities) / len(velocities)

        maximum['linear'] = max(abs(vel['lin_x']) for vel in velocities)
        maximum['angular'] = max(abs(vel['ang_z']) for vel in velocities)

    return average, maximum


def extract_planned_path(action):
    path = []
    for area in action.areas:
        path.append({'rel_id': area.id, 'name': area.name, 'type': area.type, 'floor': area.floor_number})

    return {'type': action.type, 'elevator': action.elevator, 'path': path}


def remove_duplicates(list_of_dicts, compare=None):
    seen = set()
    new_list = []

    if compare is None:
        for d in list_of_dicts:
            t = tuple(d.items())
            if t not in seen:
                seen.add(t)
                new_list.append(d)
    else:
        for d in list_of_dicts:
            t = d[compare]
            if t not in seen:
                seen.add(t)
                new_list.append(d)

    return new_list


def calculate_joypad_uses(joy_list, tolerance_in_sec):
    if joy_list:
        joy_list_without_dupes = remove_duplicates(joy_list)
        joy_list_sep_by_uses = []

        tmp_list = [joy_list_without_dupes[0]]
        prev_time = joy_list_without_dupes[0]['time']

        for joy in joy_list_without_dupes[1:]:
            if (joy['time'] - prev_time) > tolerance_in_sec:
                joy_list_sep_by_uses.append(tmp_list[:])
                tmp_list = []
            tmp_list.append(joy)
            prev_time = joy['time']

        joy_list_sep_by_uses.append(tmp_list[:])

        return joy_list_sep_by_uses
    else:
        return joy_list


def process_cov_inc_data(cov_inc):
    if cov_inc:
        start_time = cov_inc[0]['time']
        prev_time = start_time
        max_cov_x, max_cov_y, max_cov_z = cov_inc[0]['cov_x'], cov_inc[0]['cov_y'], cov_inc[0]['cov_z']
        new_cov_inc = []

        for cov in cov_inc[1:]:
            if (cov['time'] - prev_time) > 2:
                end_time = prev_time
                new_cov_inc.append({'start_time': start_time, 'end_time': end_time,
                                    'max_cov': (max_cov_x, max_cov_y, max_cov_z)})
                max_cov_x, max_cov_y, max_cov_z = cov['cov_x'], cov['cov_y'], cov['cov_z']
                start_time = cov['time']
            if cov['cov_x'] > max_cov_x:
                max_cov_x = cov['cov_x']
            if cov['cov_y'] > max_cov_y:
                max_cov_y = cov['cov_y']
            if cov['cov_z'] > max_cov_z:
                max_cov_z = cov['cov_z']
            prev_time = cov['time']

        new_cov_inc.append({'start_time': start_time, 'end_time': prev_time,
                            'max_cov': (max_cov_x, max_cov_y, max_cov_z)})

        return new_cov_inc
    else:
        return cov_inc


def calculate_avg_min_max_battery(battery_data):
    if battery_data:
        battery_matrix = np.array([[battery['wheel0'],
                                    battery['wheel1'],
                                    battery['wheel2'],
                                    battery['wheel3'],
                                    battery['wheel4']] for battery in battery_data])

        battery_matrix = battery_matrix[np.all(battery_matrix > 0.0, axis=1)]
        mins = np.min(battery_matrix, axis=0)
        maxs = np.max(battery_matrix, axis=0)
        avgs = np.average(battery_matrix, axis=0)

        return {'mins': mins.tolist(), 'maxs': maxs.tolist(), 'avgs': avgs.tolist()}
    else:
        return {'mins': [], 'maxs': [], 'avgs': []}


# noinspection PyProtectedMember
def extract_bag_data(bag):
    print_info = False

    # Get rosbag info data
    query_vars = yaml.load(bag._get_yaml_info(), Loader=yaml.BaseLoader)
    date = time.localtime(float(query_vars['start']))
    query_vars['year'] = date.tm_year
    query_vars['month'] = date.tm_mon
    query_vars['day'] = date.tm_mday

    # extract topic information
    goals = []
    experiments = []
    velocities = []
    driving_actions = []
    exp_feedback = []
    all_actions = []
    poses = []
    joy_cmd_vel = []
    cov_inc = []
    smart_wheel_battery = []
    goals_pos = []

    for topic, msg, t in bag.read_messages(topics=['/ropod/goto/result',
                                                   '/ropod/goto/goal',
                                                   '/route_navigation/goal'
                                                   '/ropod/execute_experiment/result',
                                                   '/ropod/execute_experiment/feedback',
                                                   '/load/cmd_vel',
                                                   '/amcl_pose',
                                                   '/collect_cart/goal',
                                                   '/collect_cart/result',
                                                   '/collect_cart/feedback',
                                                   '/napoleon_driving/current_state',
                                                   '/joypad/cmd_vel',
                                                   '/sw_ethercat_parser/data',
                                                   '/projected_scan'
                                                   ]):

        print_topic = ['/ropod/goto/result',
                       '/ropod/goto/goal',
                       '/route_navigation/goal',
                       '/ropod/execute_experiment/result',
                       '/collect_cart/goal',
                       '/collect_cart/result',
                       '/collect_cart/feedback']

        goal_topics = ['/ropod/goto/result', '/ropod/goto/goal', '/collect_cart/goal', '/collect_cart/result']

        if print_info:
            if topic in print_topic:
                print(f'Topic: {topic}, Time: {time_to_string(t.to_sec())}')

        if topic == '/ropod/execute_experiment/result':
            if msg.status.goal_id:
                exp_id = msg.status.goal_id.id.split("-")[1]
            else:
                exp_id = -1
            experiment = {'id': exp_id, 'type': msg.result.experiment_type,
                          'result': msg.result.result, 'status': Status(msg.status.status),
                          'time': int(t.to_sec())}
            experiments.append(experiment)

        elif topic in goal_topics:
            is_goal_topic = topic.endswith('goal')
            is_dock_goal = False
            if is_goal_topic:
                if msg.goal_id.id:
                    goal_id = msg.goal_id.id.split("-")[1]
                else:
                    goal_id = -1
                is_dock_goal = hasattr(msg.goal, 'load_id')
            else:
                if msg.status.goal_id.id:
                    goal_id = msg.status.goal_id.id.split('-')[1]
                else:
                    goal_id = -1
            goal = None
            if goal_id != -1:
                for g in goals:
                    if g['id'] == goal_id:
                        goal = g
                        break
            if goal:
                if is_goal_topic:
                    goal['action'] = extract_planned_path(msg.goal.action)
                    if is_dock_goal:
                        goal['load_id'] = msg.goal.load_id
                        goal['load_type'] = msg.goal.load_type
                else:
                    goal['status'] = Status(msg.status.status)
            else:
                if is_goal_topic:
                    tmp_goal = {'id': goal_id, 'action': extract_planned_path(msg.goal.action),
                                'time': int(t.to_sec())}
                    if is_dock_goal:
                        tmp_goal['load_id'] = msg.goal.load_id
                        tmp_goal['load_type'] = msg.goal.load_type
                    goals.append(tmp_goal)
                else:
                    goals.append({'id': goal_id, 'status': Status(msg.status.status),
                                  'time': int(t.to_sec())})

        elif topic == '/route_navigation/goal':
            goals_pos.append({'start_x': round(msg.start.pose.position.x, 6),
                              'start_y': round(msg.start.pose.position.y, 6),
                              'goal_x': round(msg.goal.pose.position.x, 6),
                              'goal_y': round(msg.goal.pose.position.y, 6)})

        elif topic == '/ropod/execute_experiment/feedback':
            if exp_feedback:
                if (exp_feedback[-1]['command_name'] != msg.feedback.command_name
                        or exp_feedback[-1]['state'] != msg.feedback.state):
                    exp_feedback.append({'command_name': msg.feedback.command_name,
                                         'state': msg.feedback.state})
                    all_actions.append({'command_name': msg.feedback.command_name,
                                        'state': msg.feedback.state, 'time': int(t.to_sec())})
            else:
                exp_feedback.append({'command_name': msg.feedback.command_name,
                                     'state': msg.feedback.state})
                all_actions.append({'command_name': msg.feedback.command_name,
                                    'state': msg.feedback.state, 'time': int(t.to_sec())})

        elif topic == '/load/cmd_vel':
            vel = {'lin_x': round(msg.linear.x, 6),
                   'lin_y': round(msg.linear.y, 6),
                   'ang_z': round(msg.angular.z, 6),
                   'time': int(t.to_sec())}
            velocities.append(vel)

        elif topic == '/napoleon_driving/current_state':
            if driving_actions:
                if driving_actions[-1]['action'] != msg.data:
                    driving_actions.append({'action': msg.data})
                    all_actions.append({'action': msg.data, 'time': int(t.to_sec())})
            else:
                driving_actions.append({'action': msg.data})
                all_actions.append({'action': msg.data, 'time': int(t.to_sec())})

        elif topic == '/collect_cart/feedback':
            all_actions.append({'goal_id': msg.status.goal_id.id.split('-')[1],
                                'action_type': msg.feedback.feedback.action_type,
                                'action_state': msg.feedback.feedback.status.sm_state,
                                'action_status_code': FeedbackStatus(msg.feedback.feedback.status.status_code),
                                'time': int(t.to_sec())})
        elif topic == '/amcl_pose':
            if msg.pose.covariance[0] > 0.5 or msg.pose.covariance[7] > 0.5 or msg.pose.covariance[35] > 0.5:
                cov_inc.append({'cov_x': round(msg.pose.covariance[0], 6),
                                'cov_y': round(msg.pose.covariance[7], 6),
                                'cov_z': round(msg.pose.covariance[35], 6),
                                'time': int(t.to_sec())})
            if poses:
                if poses[-1]['time'] != int(t.to_sec()):
                    poses.append({'pos_x': round(msg.pose.pose.position.x, 6),
                                  'pos_y': round(msg.pose.pose.position.y, 6),
                                  'orien_z': round(msg.pose.pose.orientation.z, 6),
                                  'orien_w': round(msg.pose.pose.orientation.w, 6),
                                  'time': int(t.to_sec())})
            else:
                poses.append({'pos_x': round(msg.pose.pose.position.x, 6),
                              'pos_y': round(msg.pose.pose.position.y, 6),
                              'orien_z': round(msg.pose.pose.orientation.z, 6),
                              'orien_w': round(msg.pose.pose.orientation.w, 6),
                              'time': int(t.to_sec())})

        elif topic == '/joypad/cmd_vel':
            if msg.linear.x != 0.0 or msg.linear.y != 0.0 or msg.angular.z != 0.0:
                joy_cmd_vel.append({'lin_x': msg.linear.x, 'lin_y': msg.linear.y,
                                    'ang_z': msg.angular.z, 'time': int(t.to_sec())})
        elif topic == '/sw_ethercat_parser/data':
            if smart_wheel_battery:
                if smart_wheel_battery[-1]['time'] != int(t.to_sec()):
                    smart_wheel_battery.append({'time': int(t.to_sec()), 'wheel0': msg.sensors[0].voltage_bus,
                                                'wheel1': msg.sensors[1].voltage_bus,
                                                'wheel2': msg.sensors[2].voltage_bus,
                                                'wheel3': msg.sensors[3].voltage_bus,
                                                'wheel4': msg.sensors[4].voltage_bus})
            else:
                smart_wheel_battery.append({'time': int(t.to_sec()), 'wheel0': msg.sensors[0].voltage_bus,
                                            'wheel1': msg.sensors[1].voltage_bus, 'wheel2': msg.sensors[2].voltage_bus,
                                            'wheel3': msg.sensors[3].voltage_bus, 'wheel4': msg.sensors[4].voltage_bus})

    query_vars['avg_vel'], query_vars['max_vel'] = calculate_avg_max_speed(velocities)
    query_vars['velocities'] = remove_duplicates(velocities, 'time')
    query_vars['goals'] = goals
    query_vars['goals_pos'] = goals_pos
    query_vars['experiments'] = experiments
    query_vars['all_actions'] = all_actions
    query_vars['poses'] = poses
    query_vars['joypad_uses'] = calculate_joypad_uses(joy_cmd_vel, 3)
    query_vars['cov_inc'] = process_cov_inc_data(cov_inc)
    query_vars['battery_stats'] = calculate_avg_min_max_battery(smart_wheel_battery)

    return query_vars


def write_bag_to_db(bagfile, template_env, db):
    try:
        bag = rosbag.Bag(bagfile, 'r')
    except rosbag.bag.ROSBagUnindexedException:
        print(f"SKIPPING NOT INDEXED BAGFILE {bagfile}!")
        return 1

    data = extract_bag_data(bag)

    # create queries with data
    write_template = template_env.get_template("write.cyp.jinja")
    batch_create_pose_template = template_env.get_template("batch_create_pose.cyp.jinja")
    batch_create_velocity_template = template_env.get_template("batch_create_velocity.cyp.jinja")

    main_query = write_template.render(data)
    pose_query = batch_create_pose_template.render(data)
    velocity_query = batch_create_velocity_template.render(data)

    # submit query to database
    db.write_query(main_query)
    db.write_query(pose_query)
    db.write_query(velocity_query)

    bag.close()

    return 0


def main():
    bag_directory = '/media/marc/Datenplatte/bags/'

    files_list = get_file_names(bag_directory)

    # Create jinja template loading environment
    template_loader = jinja2.FileSystemLoader('./templates/')
    template_env = jinja2.Environment(loader=template_loader)

    # Create database connection
    db = Database("chatbot", "chatbot")

    bagfile_counter = 1
    num_bagfiles = len(files_list)
    err_bagfiles = []

    for bagfile in files_list:
        print(f'Reading bagfile {bagfile_counter} of {num_bagfiles} from location {bagfile}\n')
        code = write_bag_to_db(bagfile, template_env, db)
        if code == 0:
            print('Bagfile successfully stored in database!\n')
        else:
            err_bagfiles.append(bagfile)
        bagfile_counter += 1

    # Close database connection
    db.close()


def osm_data_to_db():
    osmhandler = OSMHandler()
    osmhandler.apply_file('./map/brsu.osm')

    # Create jinja template loading environment
    template_loader = jinja2.FileSystemLoader('./templates/')
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template("osm.cyp.jinja")

    # Create database connection
    db = Database("chatbot", "chatbot")

    data = {'relations': osmhandler.osm_data}

    # create query with data
    query = template.render(data)

    # submit query to database
    db.write_query(query)


if __name__ == '__main__':
    main()
