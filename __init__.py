import json
import logging
import requests


"""
    Implementation of the Postcode API in Python using the requests library.
    Based on the pyPostcode library by Stefan Jansen. See his github repo
    for more information: https://github.com/steffex/pyPostcode/
"""


class pyPostcodeException(Exception):

    def __init__(self, id, message):
        self.id = id
        self.message = message


class Api(object):

    """ Object representation of the Postcode API functionality """

    def __init__(self, api_key):
        if api_key is None or api_key is "":
            raise pyPostcodeException(
                0, "Please request an api key on http://postcodeapi.nu"
            )

        self.api_key = api_key
        self.url = "https://postcode-api.apiwise.nl/v2/"

    def handleresponseerror(self, status):

        """ Helper function for handling HTTP errors """

        if status == 401:
            msg = "Access denied! API-key missing or invalid."
        elif status == 404:
            msg = "No result found."
        elif status == 500:
            msg = "Unknown API error."
        else:
            msg = "dafuq?"

        raise pyPostcodeException(status, msg)

    def request(self, path):

        """ Helper function for HTTP GET requests to the API """

        headers= {
            "Accept": "application/json",
            "X-Api-Key": self.api_key
        }

        req = requests.get(self.url+path, headers=headers)

        res = req.text

        if req.status_code is not 200:
            req.close()
            self.handleresponseerror(req.status_code)
        req.close()

        jsondata = json.loads(res)

        data = jsondata.get('_embedded', {}).get('addresses', [])
        if data:
            data = data[0]
        else:
            data = None

        return data


    def getaddress(self, postcode, house_number=None):

        """ Get information about a specific address """

        if house_number is None:
            house_number = ""

        path = "addresses/?postcode={0}&number={1}".format(
            str(postcode), str(house_number)
        )

        try:
            data = self.request(path)
        except pyPostcodeException as ex:
            logging.error(
                "Error looking up address {0} {1}. {2} {3}".format(
                    postcode, house_number or "", ex.id, ex. message
                )
            )
            data = None
        except Exception as ex:
            logging.exception(ex)
            data = None

        if data is not None:
            return Resource(data)
        else:
            return False


class Resource(object):

    def __init__(self, data):
        self._data = data

    @property
    def street(self):
        return self._data['street']

    @property
    def house_number(self):
        '''
        House number can be empty when postcode search
        is used without house number
        '''
        return self._data.get('number', self._data.get('house_number'))

    @property
    def postcode(self):
        return self._data.get('postcode')

    @property
    def town(self):
        return self._data.get('city', {}).get('label', self._data.get('town'))

    @property
    def municipality(self):
        result = self._data.get('municipality', {})
        if isinstance(result, dict):
            result = result.get('label')
        return result

    @property
    def province(self):
        result = self._data.get('province', {})
        if isinstance(result, dict):
            result = result.get('label')
        return result

    def _get_geo_coordinates(self, geo_type):
        return self._data.get('geo', {}).get('center', {}).get(geo_type)\
            .get('coordinates', [None, None])

    @property
    def latitude(self):
        if self._data.get('latitude'):
            return self._data.get('latitude')
        return self._get_geo_coordinates('wgs84')[0]

    @property
    def longitude(self):
        if self._data.get('longitude'):
            return self._data.get('longitude')
        return self._get_geo_coordinates('wgs84')[1]

    @property
    def x(self):
        if self._data.get('x'):
            return self._data.get('x')
        return self._get_geo_coordinates('rd')[0]

    @property
    def y(self):
        if self._data.get('y'):
            return self._data.get('y')
        return self._get_geo_coordinates('rd')[1]

    @property
    def year(self):
        return self._data.get('year')
