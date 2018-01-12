# import the basic python packages we need
import os
import sys
import tempfile
import yaml
import json
import csv
import argparse
# Temporary questionlist, Will replace once pytan bug fixed
saved_question_list = [u'Computer Name']
# disable python from generating a .pyc file
sys.dont_write_bytecode = True
# change me to the path of pytan if this script is not running from EXAMPLES/PYTAN_API
pytan_loc = "~/gh/pytan"
pytan_static_path = os.path.join(os.path.expanduser(pytan_loc), 'lib')

# Determine our script name, script dir
my_file = os.path.abspath(sys.argv[0])
my_dir = os.path.dirname(my_file)

# try to automatically determine the pytan lib directory by assuming it is in '../../lib/'
parent_dir = os.path.dirname(my_dir)
pytan_root_dir = os.path.dirname(parent_dir)
lib_dir = os.path.join(pytan_root_dir, 'lib')

# add pytan_loc and lib_dir to the PYTHONPATH variable
path_adds = [lib_dir, pytan_static_path]
[sys.path.append(aa) for aa in path_adds if aa not in sys.path]

# import pytan
import pytan

clientcreds = []
democreds = []


def get_filename():
    """Parses the command line inputs
                     Args:
                        Takes in the command line arguments

                     Returns:
                        args.configfilepath: Config file path argument
                        args.csvfilepath: Csv File Path Argument
                     """
    parser = argparse.ArgumentParser()
    parser.add_argument('configfilepath', type=str)
    parser.add_argument('csvfilepath', type=str)
    args = parser.parse_args()
    return args.configfilepath, args.csvfilepath


def load_config(configfile):
    """Loads the configuration file provided to the command line
                     Args:
                         configfile: Path to the config fill being used

                     Returns:
                        Creates two lists of the credentials one for each side of the exchange
                     """
    with open(configfile, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
    clientcreds.append(cfg['client_credentials']['username'])

    clientcreds.append(cfg['client_credentials']['password'])
    clientcreds.append(cfg['client_credentials']['host'])
    clientcreds.append(cfg['client_credentials']['port'])
    democreds.append(cfg['demo_credentials']['username'])
    democreds.append(cfg['demo_credentials']['password'])
    democreds.append(cfg['demo_credentials']['host'])
    democreds.append(cfg['demo_credentials']['port'])


def create_dashboard(question_names, name):
    """Creates dashboard with the provided name and question

                 Args:
                     question_names: List of question names that will be put in dashboard
                     name: Name of the dashboard that is being made

                 Returns:
                    creates a dashboard
                 """
    handler_args = dict()
    # Client credentials
    handler_args['username'] = clientcreds[0]
    handler_args['password'] = clientcreds[1]
    handler_args['host'] = clientcreds[2]
    handler_args['port'] = clientcreds[3]  # optional
    # Log level: 0 is only errors and warnings 12 is everything
    handler_args['loglevel'] = 0

    handler_args['debugformat'] = False

    handler_args['record_all_requests'] = True

    # instantiate a handler using all of the arguments in the handler_args dictionary
    handler = pytan.Handler(**handler_args)
    # Take input list of saved questions and creat dashboard from them
    dash_kwargs = dict()
    dash_kwargs['sqs'] = question_names
    handler.create_dashboard(name, text='', group='', public_flag=True, **dash_kwargs)


def ask_for_saved_questions(saved_questions_list):
    """Asks demo for the details of the questions that demo has that client side doesnt

             Args:
                 saved_questions_list: list of questions not on client to ask demo for details about

             Returns:
                 Writes json results to 'saved_questions_list.json'
             """
    # Asks the demo enviroment for the saved questions and their details that the client side is missing
    if len(saved_questions_list) == 0:
        return 0
    print "Questions to Make"
    print saved_questions_list
    handler_args = dict()
    # establish our connection info for the Tanium Server
    # Demo credentials
    handler_args['username'] = democreds[0]
    handler_args['password'] = democreds[1]
    handler_args['host'] = democreds[2]
    handler_args['port'] = democreds[3]  # optional

    handler_args['loglevel'] = 0

    handler_args['debugformat'] = False

    handler_args['record_all_requests'] = True

    # instantiate a handler using all of the arguments in the handler_args dictionary
    handler = pytan.Handler(**handler_args)

    # setup the arguments for the handler() class
    kwargs = dict()
    kwargs["objtype"] = u'saved_question'
    kwargs["name"] = saved_questions_list

    response = handler.get(**kwargs)

    # call the export_obj() method to convert response to JSON and store it in out
    export_kwargs = dict()
    export_kwargs['obj'] = response
    export_kwargs['export_format'] = 'json'

    out = handler.export_obj(**export_kwargs)
    with open('saved_questions_list.json', 'w') as outfile:
        outfile.write(out)
    return 1


def check_to_see_if_exists(savedlist):
    """Checks to see if questions submitted are already contained in client, outputs list of those that are not

          Args:
              savedlist: list of questions from demo to check against client questions

          Returns:
              newlist: list of all the questions not on client that are on demo
          """

    # create a dictionary of arguments for the pytan handler
    newlist = savedlist[:]
    handler_args = dict()
    # Client credentials
    handler_args['username'] = clientcreds[0]
    handler_args['password'] = clientcreds[1]
    handler_args['host'] = clientcreds[2]
    handler_args['port'] = clientcreds[3]  # optional

    handler_args['loglevel'] = 0

    handler_args['debugformat'] = False

    handler_args['record_all_requests'] = True

    # instantiate a handler using all of the arguments in the handler_args dictionary
    handler = pytan.Handler(**handler_args)

    # setup the arguments for the handler() class
    kwargs = dict()
    kwargs["objtype"] = u'saved_question'

    response = handler.get_all(**kwargs)

    # call the export_obj() method to convert response to JSON and store it in out
    export_kwargs = dict()
    export_kwargs['obj'] = response
    export_kwargs['export_format'] = 'json'

    out = handler.export_obj(**export_kwargs)
    with open('saved_questions_list', 'w') as outfile:
        outfile.write(out)

    with open("saved_questions_list") as fh:
        put = json.loads(fh.read())
    i = 1

    while i <= len(put["saved_question"]):
        q = (i - 1)
        for question in savedlist:
            if question == put["saved_question"][q]["name"]:
                newlist.remove(question)
        i = i + 1

    return newlist


# Used in create_saved_questions -- Not currently working
def tempquestionask(question_name):
    """Asks a question of Demo in order to generate json for creation of question on demo

       Args:
           question_name: Name of the question to ask

       Returns:
           results: Json of the results from asking of one question
       """
    handler_args = dict()
    # establish our connection info for the Tanium Server
    # Demo credentials
    handler_args['username'] = democreds[0]
    handler_args['password'] = democreds[1]
    handler_args['host'] = democreds[2]
    handler_args['port'] = democreds[3]  # optional

    handler_args['loglevel'] = 0

    handler_args['debugformat'] = False

    handler_args['record_all_requests'] = True

    # instantiate a handler using all of the arguments in the handler_args dictionary
    handler = pytan.Handler(**handler_args)

    # setup the arguments for the handler() class
    kwargs = dict()
    kwargs["objtype"] = u'saved_question'
    kwargs["name"] = question_name

    orig_objs = handler.get(**kwargs)

    export_kwargs = dict()
    export_kwargs['obj'] = orig_objs
    export_kwargs['export_format'] = 'json'
    export_kwargs['report_dir'] = tempfile.gettempdir()

    print "...CALLING: handler.export_to_report_file() with args: {}".format(export_kwargs)
    json_file, results = handler.export_to_report_file(**export_kwargs)

    return results


# An attempt to build saved questions not on customer console -- Not currently working
def create_saved_questions(number, savedlist):
    """Create any questions that exist on the Demo enviroment but not on the Client side that are in the Demo dashboards
        needed to be created

       Args:
           number: Number of questions needed to be made
           savedlist: Names of the questions needed to be Created

       Returns:
           nothing if number = 0
           Creates the questions needed on client side
       """
    if number == 0:
        return
    handler_args = dict()

    # establish our connection info for the Tanium Server
    # Client credentials
    handler_args['username'] = clientcreds[0]
    handler_args['password'] = clientcreds[1]
    handler_args['host'] = clientcreds[2]
    handler_args['port'] = clientcreds[3]  # optional

    handler_args['loglevel'] = 0

    handler_args['debugformat'] = False

    handler_args['record_all_requests'] = False

    # Instantiate a handler using all of the arguments in the handler_args dictionary
    print savedlist
    handler = pytan.Handler(**handler_args)
    # Move through each saved question to make and make a json of it to send to client to make saved question
    for saved_question in savedlist:
        # setup the arguments for the handler.get() method
        question_results = tempquestionask(saved_question)
        with open('Result.json', 'w') as outfile:
            outfile.write(question_results)
        # create the object from the exported JSON file
        create_kwargs = dict()
        create_kwargs['objtype'] = u'saved_question'
        create_kwargs['json_file'] = "Result.json"
        handler.create_from_json(**create_kwargs)


def demo_dashboard_loading(cs):
    """Get all the dashboards from the client and compare them to those from the Demo csv any dashboards in demo not
    in the client get added to a list.

    Args:
        cs: Path to the csv file containing all of the Demo Dashboards and questions

    Returns:
        dash_boards_on_demo: List of dashboards that need to be made on the Client side
        num: number of dashboards needed (used as a check to see if the program has to go further)
    """
    handler_args = dict()
    # Client Credentials
    handler_args['username'] = clientcreds[0]
    handler_args['password'] = clientcreds[1]
    handler_args['host'] = clientcreds[2]
    handler_args['port'] = clientcreds[3]  # optional

    handler_args['loglevel'] = 0

    handler_args['debugformat'] = False

    handler_args['record_all_requests'] = True

    # instantiate a handler using all of the arguments in the handler_args dictionary
    handler = pytan.Handler(**handler_args)
    dash_kwargs = dict()
    dash_kwargs['sqs'] = saved_question_list
    # DELETE ONCE PYTAN IS FIXED
    # This is a temporary dashboard necessary to circumvent the bug
    handler.create_dashboard("Oh no isa bug", text='', group='', public_flag=True,
                             **dash_kwargs)
    handler.delete_dashboard("Oh no isa bug", **dash_kwargs)
    obj, results = handler.get_dashboards()
    dash_boards_on_demo = {}
    with open(cs) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            dashboard, question = row['name'], row['questionname']
            if dashboard not in dash_boards_on_demo:
                dash_boards_on_demo[dashboard] = [question]
            else:
                dash_boards_on_demo[dashboard].append(question)
    key = dash_boards_on_demo.keys()
    dashboards_not_to_make = []
    i = 1
    while i <= len(results):
        q = (i - 1)
        for item in key:
            if item == (results[q]["name"]):
                dashboards_not_to_make.append(item)
        i = i + 1
    for dashs in dashboards_not_to_make:
        dash_boards_on_demo.pop(dashs, None)
    if len(dash_boards_on_demo) == 0:
        num = 0
    else:
        num = 1
    # Returns 1 if there are dashboards to make, Return 0 if not
    return dash_boards_on_demo, num


def main():
    config, csv_file = get_filename()
    load_config(config)
    # Formatting of the csv to make it usable by the script
    with open(sys.argv[2], 'r') as fh:
        lines = fh.readlines()
    with open("temp.csv", 'w') as f:
        f.write("name,dashboard_id,questionname,saved_question_id")
    with open("temp.csv", 'r') as fh:
        lin = fh.readlines()
    new = [lin[0]] + lines[3:-2]
    with open(csv_file, 'w') as f:
        f.writelines(new)
    dashboards_to_make, number_of_dashboards_needed = demo_dashboard_loading(csv_file)
    if number_of_dashboards_needed == 0:
        print "No Dashboards to Make"
        return
    list_of_questions = dashboards_to_make.values()
    # Shows user what dashboards are in the process of being made
    print "Dashboards To Make"
    print dashboards_to_make
    for items in list_of_questions:
        checkedlist = check_to_see_if_exists(items)
    # Used to figure out if there is a diffrence in saved questions between client and demo
    number = ask_for_saved_questions(checkedlist)
    # Not working currently, That is why there is a error catch
    try:
        create_saved_questions(number, checkedlist)
    except:
        print "error building saved questions (may not exist on customer console)"
    for dash in dashboards_to_make.keys():
        dashboards = dashboards_to_make[dash]
        create_dashboard(dashboards, dash)
    # Removes unnecessary artifacts
    os.remove("temp.csv")
    os.remove("saved_questions_list")


if __name__ == '__main__':
    main()
