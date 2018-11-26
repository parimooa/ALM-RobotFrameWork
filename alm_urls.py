class ALMUrls(object):
    """
    class of all ALM Urls
    All Urls should go here
    """

    def __init__(self, domains, projects):
        self.domains = domains
        self.domain_url = None
        self.projects = projects
        self.project_url = None
        self.test_case = None
        self.tc_design_steps = None
        self.run_id = None
        self.run_step_id = None

    @property
    def alm_base_url(self):
       return "https://127.0.0.1:8443/qcbin"

    @property
    def alm_rest_base_url(self):
        return self.alm_base_url + "/rest"

    @property
    def alm_site_session(self):
        return self.alm_rest_base_url + "/site-session"

    @property
    def alm_auth_point(self):
        return self.alm_base_url + "/authentication-point"

    @property
    def qc_auth(self):
        return self.alm_auth_point + "/authenticate"

    @property
    def domain(self):
        self.domain_url = self.alm_rest_base_url + "/domains/" + self.domains
        return self.domain_url

    @property
    def project(self):
        self.project_url = self.domain + "/projects/" + self.projects
        return self.project_url

    @property
    def alm_tests(self):
        if self.project:
            return self.project + "/tests?page-size=max"
        else:
            print ("Either domain or  project is not set")

    @property
    def alm_ready_tests(self):
        if self.project:
            return self.project + "/tests?query={status['Ready to Test']}&page-size=max"
        else:
            print ("Either domain or  project is not set")

    @property
    def alm_test_case(self):
        return self.test_case

    @alm_test_case.setter
    def alm_test_case(self, tc_id):
        if tc_id:
            self.test_case = self.alm_tests + "/" + str(tc_id)

    @property
    def alm_tc_design_step(self):
        return self.tc_design_steps

    @alm_tc_design_step.setter
    def alm_tc_design_step(self, tc_id):
        if tc_id:
            self.tc_design_steps = self.project + "/design-steps?query={parent-id[" + tc_id + "]}"

    @property
    def alm_logout_url(self):
        return self.alm_auth_point + "/logout"

    @property
    def alm_test_set_folders(self):
        if self.project:
            return self.project + "/test-set-folders"
        else:
            print ("Either domain or  project is not set")

    @property
    def alm_test_sets(self):
        if self.project:
            return self.project + "/test-sets"
        else:
            print ("Either domain or  project is not set")

    @property
    def alm_test_instances(self):
        if self.project:
            return self.project + "/test-instances"
        else:
            print ("Either domain or  project is not set")

    @property
    def alm_test_run_url(self):
        if self.project:
            return self.project + "/runs"
        else:
            print ("Either domain or  project is not set")

    @property
    def alm_test_run(self):
        return self.run_id

    @alm_test_run.setter
    def alm_test_run(self, run_id):
        if run_id:
            self.run_id = self.alm_test_run_url + "/" + str(run_id)

    @property
    def alm_test_run_step(self):
        return self.run_step_id

    @alm_test_run_step.setter
    def alm_test_run_step(self, run_step_id):
        if run_step_id:
            self.run_step_id = self.alm_test_run + "/run-steps/" + str(run_step_id)

    @property
    def alm_test_steps(self):
        if self.project:
            return self.project + "/design_steps"
        else:
            print ("Either domain or  project is not set")
