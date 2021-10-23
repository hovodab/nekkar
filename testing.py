import pymongo
from netaddr import IPNetwork, IPAddress


class NetworkRepository(object):
    def __init__(self):
        self.myclient = pymongo.MongoClient("mongodb://localhost:27017/")

    def create_record(self, subnet, as_name):
        network = IPNetwork(subnet)
        first = network[0].value
        last = network[-1].value
        mydb = self.myclient["lookup_db"]
        return mydb["asrecords"].insert_one({
            "subnet": subnet,
            "AS_name": as_name,
            "first": first,
            "last": last
        })

    def get_by_ip(self, ip_address):
        ip = IPAddress(ip_address)
        return list(self.myclient["lookup_db"]["asrecords"].find(
            {
                "first": {"$lte": ip.value},
                "last": {"$gte": ip.value},
            }
        ))


if __name__ == "__main__":
    repo = NetworkRepository()
    # repo.create_record(subnet="122.150.0.0/24", as_name="AS1")
    print(repo.get_by_ip("122.150.0.15"))
