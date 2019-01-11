from requests import Session

class Client():

    def __init__(self,backend):
        self.s = Session()
        self.backend = backend

    def get_json(self,path):
        return self.s.get(self.backend + path).json()