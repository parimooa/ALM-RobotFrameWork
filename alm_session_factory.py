import requests
from alm_urls import ALMUrls
#from alm_session import ALMSTARTException


class SingletonType(type):
    """
    singleton pattern 
    """

    def __call__(cls, *args, **kwargs):
        try:
            return cls.__instance
        except AttributeError:
            cls.__instance = super(SingletonType, cls).__call__(*args, **kwargs)
            return cls.__instance


class ALMSessionFactory(object):
    # singleton making sure same instance is returned for multiple calls
    __metaclass__ = SingletonType

    def __init__(self, domain, project):
        """
        
        :param domain: domain name in ALM
        :param project: project name in ALM
        """
        # create request session object
        self.alm_session = requests.session()
        self.urls = ALMUrls(domain, project)

    def connect(self):
        """
        creates the connection object with the basic authorisation header
        first "GET" call returns the cookie 
        second "POST" call to  site/session creating the QCSession cookie
        Cookie allows application to access the QC services/resources
        :return: 
        """

        headers = {
            'cache-control': "no-cache",
            'authorization': "Basic OTY5MzT58LKaEFuOTY5MyE2",  # replace this with basic auth of user
        }

        response = self.alm_session.get(self.urls.qc_auth, headers=headers, verify=False, timeout=10)

        if response.status_code == 200:
            session = self.alm_session.post(self.urls.alm_site_session,
                                            cookies=self.alm_session.cookies.get_dict())
            if session.status_code == 201:  # returns 201 when QCSession cookie is created
                cookies = self.alm_session.cookies
                return self.alm_session
        else:
            raise Exception("session not created", response.status_code, response.text)

    def logout(self,session):
        """
        logs out user from ALM session
        Args:
            session: Active session with valid cookies

        Returns:

        """
        response = session.get(self.urls.alm_logout_url)
        if response.status_code== 200:
            print ("Logout session successfull")

        else:
            raise Exception("Logout failed !! ", response.text)
