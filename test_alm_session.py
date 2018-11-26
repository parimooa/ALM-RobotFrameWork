from alm_session import ALMSession
import pytest
import collections


class TestALMSession(object):
    def setup_class(cls):
        cls.alm_session = ALMSession()
        cls.test_tc_id = 620
        cls.test_run_id = 7
        cls.non_existent_id = 0
        cls.test_case_ids = [2345, 1720]
        cls.test_case_ids_non_existent = [88888, 99999]

    def test_get_all_testcases_fetches_all_tests(self):
        test_cases = self.alm_session.get_all_tests()
        assert test_cases

    def test_design_steps_are_in_the_order_of_test_ids(self):
        response = self.alm_session.get_bulk_design_steps(self.test_case_ids)
        response_test_id = [int(x['values'][0]['value']) for fields in response['entities'] for x in fields['Fields'] if
            x['Name'] == 'parent-id']
        response_test_ids=sorted(set(response_test_id),key=response_test_id.index) # preserve the order
        assert response_test_ids == self.test_case_ids , " returned test case ids are not in order with given test ids"

    def test_design_steps_are_ordered(self):
        ordered_list = self.alm_session.get_ordered_design_steps(self.test_case_ids)
        step_order = [x['step-order'] for x in ordered_list]
        sorted_list = sorted(ordered_list, key=lambda k: int(k['step-order']))
        sorted_step_order = [x['step-order'] for x in sorted_list]
        assert step_order == sorted_step_order, "step orders are not in order"

    def test_design_steps_ordered_fails_for_non_existent_id(self):
        ordered_list = self.alm_session.get_ordered_design_steps(self.test_case_ids_non_existent)
        assert not ordered_list, "Non existent test id's fetched design steps"

    def test_get_design_steps(self):
        design_steps = self.alm_session.get_bulk_design_steps(self.test_case_ids)
        assert design_steps['entities'], "test id's did not fetch design steps"

    def test_get_design_steps_fails_for_non_existent_id(self):
        design_steps = self.alm_session.get_bulk_design_steps(self.test_case_ids_non_existent)
        assert not design_steps['entities'], "Non existent test id's fetched design steps"

    @pytest.mark.skip(reason="Requires implementation of clean up / Delete  method in API ")
    def test_create_test_set_folder(self):
        response = self.alm_session.create_test_set_folder()
        assert response, "failed to create tests set folder"

    @pytest.mark.skip(reason="Requires implementation of clean up / Delete  method in API ")
    def test_update_test_run_result(self):
        result_json = [{'id': 7, 'status': 'Passed'}]
        response = self.alm_session.update_test_run_result(result_json)
        assert response, " failed to update result"

    @pytest.mark.skip(reason="Requires implementation of clean up / Delete  method in API ")
    def test_update_test_run_step_result(self):
        result_json = [{"run_id": 100,
                        "test_steps": [{"id": 123, "status": "Passed"}, {"id": 231, "status": "Failed"}]
                        },
                       {"run_id": 101,
                        "test_steps": [{"id": 200, "status": "No Run"}, {"id": 201, "status": "Failed"}]
                        }
                       ]
        response = self.alm_session.update_test_run_result(result_json)
        assert response, " failed to update run result"

    @pytest.mark.skip(reason="Requires implementation of clean up / Delete  method in API ")
    def test_create_test_instances(self):
        response = self.alm_session.create_test_instances(cls.test_case_ids)
        assert response, " failed to create test instances"

    def test_create_test_instance_fails_for_non_existent_id(self):
        with pytest.raises(Exception) as exc_info:
            response = self.alm_session.create_test_instances(self.test_case_ids_non_existent)
        assert 'qccore.general-error' in exc_info.value[1], "instance created for an invalid test case id"

    def test_is_session_check_passes_for_active_session(self):
        assert self.alm_session.is_session_active() ,"session check fails for active connection"

    def test_is_session_check_passes_for_stale_session(self):
        self.alm_session.alm_logout()
        assert not self.alm_session.is_session_active() ,"session check fails for stale connection"

