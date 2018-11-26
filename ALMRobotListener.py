from alm_robot_decorator import post_alm_result
from robot.libraries.BuiltIn import BuiltIn

# get the value of variable from robot file and convert to int since robot sends as strings
skip = int(BuiltIn().get_variable_value('${skip_alm_post}'))


class ALMRobotListener(object):
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self):
        self.ROBOT_LIBRARY_LISTENER = self

    # decorate function with decorator
    @post_alm_result(skip=skip)
    def _end_test(self, name, attrs):
        """
        decorator for skipping posting result to alm. 
        if skip is true  result is not posted 
        
        Args:
            name: name of the test
            attrs: attributes of test

        Returns:attrs dictionary

        """
        return attrs

    @post_alm_result(skip=skip)
    def end_suite(self, name, attrs):
        """
        decorator for skipping posting result to alm. 
        if skip is true  result is not posted 

        Args:
            name: name of the test
            attrs: attributes of test

        Returns:

        """
        return attrs
