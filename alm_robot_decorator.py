from functools import wraps
from alm_session import ALMSession
import logging



logging.basicConfig(level=logging.DEBUG)


def post_alm_result(**condition):
    """
    Decorator for posting results back to ALM when condition skip is set to true
    example : condition = {'skip': True}
    Args:
        **condition: dictionary

    Returns: if condtion is true , does not processing 
             if skip condition is false, the results are posted back to ALM

    """
    # holds the results of each robot test case
    global robot_results
    robot_results = dict()

    def wrapper(func):
        print (type(condition['skip']))

        if not condition['skip']:

            @wraps(func)
            def robot_reporter(*args):

                func_attrs = func(*args)
                # checks if called func is robot's end of test case
                if func.__name__ == '_end_test':
                    # extract the ALM run id from the test name
                    alm_run_id = str(args[1].split('_')[3])
                    # now grab the result of test case
                    status = func_attrs["status"]
                    #add run id as key and status as value
                    # if run id is previously seen, just add the status as value(list)
                    robot_results.setdefault(alm_run_id, []).append(status)
                # checks if called func is robot's end suite
                if func.__name__ == 'end_suite':
                    print robot_results
                    print condition
                    print ("Posting results to ALM")
                    # creates ALM session
                    alm = ALMSession()
                    if alm:
                        print "alm session active posting results back to QC"
                        alm_status = 'Blocked'
                        alm_result_json = []
                        for key in robot_results:
                            # if any of the test is fail , whole test case is failed
                            if 'FAIL' in robot_results[key]:
                                # ALM status is Failed or Passed
                                alm_status = 'Failed'

                            else:
                                alm_status = 'Passed'
                            alm_result_json.append({"id": key, "status": alm_status})
                        #print alm_result_json
                            alm.update_test_run_result(alm_result_json)

                    else:
                        print ("Failed to set up ALM session")

            return robot_reporter
        else:
            print ("Skipping posting result to ALM")

    return wrapper
