import collections
import time

import requests

from alm_session_factory import ALMSessionFactory
from alm_urls import ALMUrls


# TODO proper logging , capture events  in a file
# logging.basicConfig(level=logging.DEBUG)


class ALMSession(ALMUrls, ALMSessionFactory):
    """
    sets the session for ALM REST API and 
    supports various methods to access ALM API resources 
    """
    ALMRun = collections.namedtuple('ALMRun', 'test_instances test_set test_ids')

    def __init__(self, domains='XXXX', projects='XXXX'):
        if domains and projects:
            ALMUrls.__init__(self, domains, projects)
            ALMSessionFactory.__init__(self, domains, projects)
            self.alm_session = self.connect()  # self.alm_session
            self.header = {'Content-type': 'application/json', 'Accept': 'application/json'}
            # self.header = {'Accept': 'application/json'}  # get response is json or default is xml
        else:
            print("Please provide domain and project name of ALM")

    def get_all_tests(self):
        """
         makes a rest call to ALM API with the QCSession cookies to fetch all test cases
        :return: json string with all the test cases within a project 
        """
        if self.alm_session.cookies:
            tests = self.alm_get(self.alm_tests)
            return tests.json()
        else:
            pass

    def get_ready_tests(self):
        """
         makes a rest call to ALM API with the QCSession cookies to fetch all test cases
        :return: json string with all the test cases within a project 
        """
        if self.alm_session.cookies:
            response = self.alm_get(self.alm_ready_tests)
            if response.status_code == 200:
                return response.json()
            else:
                raise ALMSTARTException("Unable to Fetch 'Ready To Test test cases, please check ALM connection",
                                        response.text)

    def get_test_case(self, tc_id):
        """
         fetches all attributes of a given test case id
        :param tc_id: integer
        :return: json string
        """

        if self.alm_session.cookies:
            self.alm_test_case = tc_id
            test_case = self.alm_get(self.alm_test_case)
            return test_case.json()

    def get_design_steps(self, des_id):
        """
        REST call to ALM API retrieving design steps of a given test id
        Args:
            des_id: string 

        Returns: design step json

        """

        if self.alm_session.cookies:
            self.alm_tc_design_step = des_id
            tc_des_steps = self.alm_get(self.alm_tc_design_step)
            return tc_des_steps.json()

    def setup_run(self, test_ids, **kwargs):
        """
        Accepts list of test case ids from ALM
        creates test set folder,test-set, test instances and test runs of tests ids
        retrieves the design steps of test ids
        transforms the ALM design steps nested json into a simple json and attaches created test run ids 
        Args:
            test_ids: list of test ids
            kwargs: if skip is set to True, it doesnt create any test instance and run in ALM

        Returns: list of design step dictionary with run id 

        """
        design_steps = self.get_bulk_design_steps(test_ids)
        transformed_design_steps = self.transform_nested_alm_json(design_steps['entities'])
        skip_run = kwargs.get('skip', False)
        if skip_run:
            return transformed_design_steps
        test_run_tuple = self.create_test_instances(test_ids)
        test_runs = self.create_test_run(test_run_tuple)
        transformed_test_runs = self.transform_nested_alm_json(test_runs)  # Transform nested json
        design_steps_run_ids \
            = self._attach_run_id_with_design_steps(transformed_test_runs, transformed_design_steps)
        return design_steps_run_ids

    @staticmethod
    def _attach_run_id_with_design_steps(run_ids, design_steps):
        """
        checks test ids match up and then retrieves the corresponding run id from run ids
        the run id is then added as dict item in design steps
        Please note in design steps the key parent-id is same as key test-id with run ids dictionary
        Args:
            run_ids: json string  
            design_steps: json string

        Returns: list of design steps dictionary with corresponding run id 

        """
        for steps in design_steps:
            for runs in run_ids:
                # check if test ids are same
                if steps['parent-id'] == runs['test-id']:
                    # add dictionary entry for run-id in design steps dictionary
                    steps['run-id'] = runs['id']

        return design_steps

    def get_bulk_design_steps(self, test_ids):
        """
        retrieve the design steps of all given test ids 
        Args:
            test_ids: list 

        Returns: combined design steps json

        """
        if type(test_ids) is not list:
            print ("test ids are not list type, please send test id list")
            return
        elif self.alm_session.cookies:
            tc_design_step = {}
            # convert the test ids list into string and delimit with 'or' for query string
            for test_id in test_ids:
                self.alm_tc_design_step = str(test_id)
                tc_des_steps = self.alm_get(self.alm_tc_design_step)
                if tc_des_steps.status_code == 200:
                    if 'entities' in tc_design_step:
                        for design_step in tc_des_steps.json()['entities']:
                            tc_design_step['entities'].append(design_step)
                        tc_design_step['TotalResults'] += len(tc_des_steps.json()['entities'])

                    else:
                        tc_design_step = tc_des_steps.json()
                else:
                    raise ALMSTARTException("No Design steps were retrieved, please check test cases ",
                                            tc_des_steps.json())
            return tc_design_step

    # TODO this may not be required at all.
    def get_ordered_design_steps(self, test_case_ids):
        """
        orders the test case ids
        Args:
            test_case_ids: list

        Returns:json

        """
        design_steps_json = self.get_bulk_design_steps(test_case_ids)
        design_steps = design_steps_json['entities']
        for index, steps in enumerate(design_steps):
            for Fields in steps['Fields']:
                if Fields['Name'] == 'step-order':
                    Fields['values'][0]['value'] = str(index)
        return self.transform_nested_alm_json(design_steps)

    @staticmethod
    def transform_nested_alm_json(alm_nested_json):
        """
         simplifies the nested json received from ALM 
        :param alm_nested_json: collated design steps of test cases json
        :return: list of design steps dicts
        """
        test_case = []
        test_case_json = dict()
        for Fields in alm_nested_json:
            for attribs in Fields['Fields']:
                attrib_values = ''.join([attribs['values'][0].get("value", '') if x else '' for x in attribs['values']])
                # print attribs['Name'] + "=" + attrib_values
                test_case_json[attribs['Name']] = attrib_values
            test_case.append(test_case_json)
            test_case_json = dict()
        return test_case

    def create_test_instances(self, test_case_ids):
        """
         This test instance is created within the test lab of ALM 
         PRE-REQ:Test case instance can be created only when  test set folder and test set is already created
         step 1 : Create test set folder and get id
         Step 2 : Create test set with parent id generated from step 1
        :param test_case_ids: list of test case id's to be included in test instances
        :return: json string
        """
        test_set_folder = self.create_test_set_folder()  # create test set folder json
        test_set_folder_id = self._get_id(test_set_folder)  # now extract id
        if type(test_case_ids) is not list:  # check if there is a list
            print ("test ids are not list type, please send test id list")
            return
        else:
            test_instance_ids = []
            test_set = self.create_test_set(test_set_folder_id)  # create test set with test set folder id as parent
            test_set_id = self._get_id(test_set)  # Now extract the id
            # iterate over the test ids to create test instances in a given test set /folder
            for test_id in test_case_ids:
                # TODO Figure out why the keys names should be empty for POST request, Possible bug with ALM REST API !!
                # TODO Find out how multiple objects (test ids) are sent in single JSON string
                test_instance_payload = {"Fields": [{"": "test-id", "values": [{"value": str(test_id)}]},
                                                    {"": "cycle-id", "values": [{"value": str(test_set_id)}]},
                                                    {"": "subtype-id", "values":
                                                        [{"value": "hp.qc.test-instance.MANUAL"}]}]}

                response = self.alm_post(self.alm_test_instances, test_instance_payload)
                test_instance_ids.append(self._get_id(response))
            ALMSession.ALMRun.test_instances = tuple(test_instance_ids)
            ALMSession.ALMRun.test_ids = tuple(test_case_ids)
            ALMSession.ALMRun.test_set = test_set_id
            return ALMSession.ALMRun

    def create_test_set_folder(self, test_set_folder_name="TST_"):
        # TODO Default name of folder to be decided
        """
         creates test folder within "TEST lab" of ALM  
        :param test_set_folder_name: string or defaults to "TST_" 
        :return: test set folder json string 
        """
        if self.alm_session.cookies:
            date_time = time.strftime("%d%m%Y-%H%M%S")
            test_set_folder = test_set_folder_name + date_time
            # TODO Figure out why the keys names should be empty for POST request, Possible bug with ALM REST API !!
            payload = {"Fields": [{"": "name", "values": [{"value": str(test_set_folder)}]},
                                  {"Name": "description", "values":
                                      [{"value": "created by REST API via Test Selection Tool"}]}]}

            response = self.alm_post(self.alm_test_set_folders, payload)
            # test_case_id = response.headers['location'].split('/')[10] # alternate way of getting id
            return response

    @staticmethod
    def _get_id(tests):
        """
         Extracts the id from newly created json string
        :param tests: json string   
        :return:  test id  
        """
        return next(test_id['values'][0]['value'] for test_id in tests['Fields'] if test_id['Name'] == 'id')

    @staticmethod
    def get_field_value(alm_json_string, target_field):
        """
                 Extracts the value of target_field from newly created json string
                :param tests: json string and target_field  
                :return:  value of given filed 
                """
        return next(
            test_id['values'][0]['value'] for test_id in alm_json_string['Fields'] if test_id['Name'] == target_field)

    def create_test_set(self, test_folder_id):
        """
         creates test set in "Test lab" within ALM
         test set is created within the test set folder which is passed as an argument
        :param test_folder_id: integer
        :return: json string of newly created test set
        """

        date_time = time.strftime("%d%m%Y-%H%M%S")
        test_set_name = "TST_test_set_" + date_time
        # TODO Figure out why the keys names should be empty for POST request, Possible bug with ALM REST API !!
        payload = {"Fields": [{"": "name", "values": [{"value": test_set_name}]},
                              {"": "description", "values": [{"value": "created by REST API (Test set)"}]},
                              {"": "parent-id", "values": [{"value": test_folder_id}]},
                              {"values": [{"value": "hp.qc.test-set.default"}], "": "subtype-id"}, ]}
        response = self.alm_post(self.alm_test_sets, payload)
        return response

    def create_test_run(self, test_instance_details):
        """
        Creates the test run based on the test instance details ( Test run tab of ALM)
        with default status as "Not Completed"
        Args:
            test_instance_details: is a named Tuple with test_instances, test_set  and test_ids details

        Returns: list of run ids created

        """
        if test_instance_details:
            date_time = time.strftime("%d%m%Y-%H%M%S")
            run_name = "TST_Run" + date_time
            status = 'Not Completed'
            run_ids = []
            for i, test_inst_id in enumerate(test_instance_details.test_instances):
                test_run_payload = {
                    "Fields": [{"": "test-id", "values": [{"value": str(test_instance_details.test_ids[i])}]},
                               {"": "subtype-id", "values": [{"value": "hp.qc.run.MANUAL"}]},
                               {"": "cycle-id", "values": [{"value": str(test_instance_details.test_set)}]},
                               {"": "name", "values": [{"value": run_name}]},
                               {"": "owner", "values": [{"value": "100000"}]},
                               {"": "testcycl-id", "values": [{"value": str(test_inst_id)}]},
                               {"": "status", "values": [{"value": status}]}]}

                response = self.alm_post(self.alm_test_run_url, test_run_payload)
                if response:
                    run_ids.append(response)
            if run_ids:
                print ("Test run created successfully %s", run_ids)
                return run_ids
            else:
                ALMSTARTException("No run ids were created")

    def update_test_run_result(self, run_result_list_dict):
        """
        This method updates the overall run result 
        run_result_list_dict should be in this format [{"id":123,"status":"Passed"},{"id":231,"status":"Failed"}]
        status could be either "Passed", "Failed" , "N.A", "Not Completed" , "Blocked", "No Run"
        Args:
            run_result_list_dict: list of ids , status dictionary
        Returns:

        """

        if run_result_list_dict and self.alm_session.cookies:
            for runs in run_result_list_dict:
                status_payload = {"Fields": [{"": "status", "values": [{"value": runs['status']}]}]}
                self.alm_test_run = runs["id"]
                response = self.alm_put(self.alm_test_run, status_payload)
                print (response)
        else:
            print ("Looks like run result is empty")
            raise ALMSTARTException("Looks like run result is empty")

    def update_test_run_step_result(self, test_run_result_list_dict):
        """
        This method updates the test steps results
        test_run_result_list_dict , [{ "run_id":100,
                              "test_steps":[{"id":123,"status":"Passed"},{"id":231,"status":"Failed"}]
                             },
                             { "run_id":101,
                              "test_steps":[{"id":200,"status":"No Run"},{"id":201,"status":"Failed"}]
                             }
                             ]
        status could be either "Passed", "Failed" , "N.A", "Not Completed" , "Blocked", "No Run"
        Args:
            test_run_result_list_dict: list of ids , status dictionary
        Returns:

        """
        overall_run_result = []
        results_dict = dict()
        if test_run_result_list_dict & self.alm_session.cookies:
            for runs in test_run_result_list_dict:
                for test_steps in runs["test_steps"]:
                    test_step_status_payload = {"Fields": [{"": "status", "values": [{"value": test_steps['status']}]}]}
                    self.alm_test_run = runs["run_id"]
                    self.alm_test_run_step = test_steps["id"]
                    response = self.alm_put(self.alm_test_run_step, test_step_status_payload)
                overall_status = all(
                    test_step_results['status'] == "Passed" for test_step_results in runs["test_steps"])
                results_dict["id"] = runs["run_id"]
                if overall_status:
                    results_dict["status"] = "Passed"
                else:
                    results_dict["status"] = "Failed"
                overall_run_result.append(results_dict)
                self.update_test_run_result(overall_run_result)
                results_dict = dict()
        else:
            print ("Looks like result is empty")

    # TODO implement check for check in status
    def is_checked_in(self, test_cases):
        pass

    def alm_put(self, uri, payload):
        """
         Generic PUT request
        :param uri: destination uri of ALM REST API
        :param payload: payload for request
        :return: json request on success or raises exception with response message from ALM 
        """
        if self.is_session_active():
            session = self.alm_session
        else:
            # get new connection
            session = self.connect()
        response = session.put(uri, json=payload, cookies=session.cookies, headers=self.header)
        if response.status_code == 200:
            return response.json()
        else:
            raise ALMSTARTException("Something went wrong with the PUT request", response.text)

    def alm_post(self, uri, payload):
        """
         Generic post request
        :param uri: destination uri of ALM REST API
        :param payload: payload for request
        :return: json request on success or raises exception with response message from ALM 
        """
        if self.is_session_active():
            session = self.alm_session
        else:
            # get new connection
            session = self.connect()
        response = session.post(uri, json=payload, cookies=session.cookies, headers=self.header)
        if response.status_code == 201:
            return response.json()
        else:
            raise ALMSTARTException("Something went wrong with the post request", response.text)

    def alm_get(self, uri):
        """
         Generic GET request
        :param uri: destination uri of ALM REST API
        :return: json request on success or raises exception with response message from ALM 
        """
        if self.is_session_active():
            session = self.alm_session
        else:
            # get new connection
            print("Getting new connection now !!")
            session = self.connect()
        response = session.get(uri, cookies=session.cookies, headers=self.header)
        if response.status_code == 200:
            return response
        else:
            raise ALMSTARTException("Something went wrong with the GET request", response.text)

    def is_session_active(self):
        """
        checks if ALM session is still active
        Returns: boolean True for active and False for stale session

        """
        response = requests.get(self.alm_site_session, cookies=self.alm_session.cookies, verify=False,
                                headers=self.header)
        if response.status_code == 401:
            print ("Session is not Active !!")
            return False
        elif response.status_code == 200:
            print ("Session is Active")
            return True
        else:
            raise ALMSTARTException("It is not possible to check session status , server response is  ", response.text)

    def alm_logout(self):
        self.logout(self.alm_session)


class ALMSTARTException(Exception):
    '''Raise when a specific subset of values in context of app is wrong'''

    def __init__(self, message, error_obj, *args):
        self.message = message  # without this you may get DeprecationWarning
        # Special attribute you desire with your Error,
        self.error_obj = error_obj
        # allow users initialize misc. arguments as any other builtin Error
        super(ALMSTARTException, self).__init__(message, error_obj, *args)
