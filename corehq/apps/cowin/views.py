import datetime
import json

import requests
from django.http import HttpResponse, HttpResponseBadRequest

from casexml.apps.case.xml.generator import safe_element
from xml.etree import cElementTree as ElementTree


def find_cowin_appointments(request):
    pincode = request.GET.get('pincode')
    on_date = request.GET.get('date')

    error_response = _validate_request(pincode, on_date)
    if error_response:
        return error_response

    response = _get_response(pincode, on_date)
    appointments = response.json()['sessions']
    fixtures = AppointmentResultsFixture(appointments).fixture
    return HttpResponse(fixtures, content_type="text/xml; charset=utf-8")


def _validate_request(pincode, on_date):
    if not pincode or not on_date:
        return HttpResponseBadRequest("please provide both pincode and a date")

    try:
        datetime.datetime.strptime(on_date, '%d-%m-%Y')
    except ValueError:
        return HttpResponseBadRequest("Invalid date, format should be DD-MM-YYYY")


def _get_response(pincode, on_date):
    headers = {'Accept-Language': 'en_US'}
    url = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/findByPin?" \
          f"pincode={pincode}&date={on_date}"
    return requests.get(url, headers=headers)


class AppointmentResultsFixture(object):
    id = "appointments"

    def __init__(self, appointments):
        self.appointments = appointments

    @property
    def fixture(self):
        element = safe_element("results")
        element.set('id', self.id)

        for appointment in self.appointments:
            element.append(AppointmentResultXMLGenerator(appointment).get_element())

        return ElementTree.tostring(element, encoding='utf-8')


class AppointmentResultXMLGenerator(object):
    appointment_fields = {
        # "center_id",
        "name": "Name",
        # "name_l",
        "address": "Address",
        # "address_l",
        "state_name": "State",
        # "state_name_l",
        "district_name": "District",
        # "district_name_l",
        "block_name": "Block",
        # "block_name_l",
        "pincode": "Pincode",
        # "lat",
        # "long",
        "from": "From",
        "to": "To",
        "fee_type": "Fee Type",
        "fee": "Fee",
        "session_id": "Session ID",
        "date": "Date",
        "available_capacity": "Capacity",
        "available_capacity_dose1": "First Dose",
        "available_capacity_dose2": "Second Dose",
        "min_age_limit": "Minimum Age",
        "vaccine": "Vaccine",
        "slots": "Slots"
    }

    def __init__(self, appointment):
        self.appointment = appointment

    def get_element(self):
        root = safe_element("appointment")
        for field in self.appointment_fields:
            root.append(safe_element(field, self.appointment[field]))
        return root


def send_request_for_meta_beneficiary_type_protected_api():
    headers = {
        'Accept-Language': 'en_US',
        'User-Agent': '',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Api-Key': '3sjOr2rmM52GzhpMHjDEE1kpQeRxwFDr4YcBEimi'
    }

    url = "https://cdndemo-api.co-vin.in/api/v2/registration/beneficiary/idTypes"
    return requests.get(url, headers=headers)


def send_request_for_otp_protected_api(mobile_number=None):
    headers = {
        'Accept-Language': 'en_US',
        'User-Agent': '',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Api-Key': '3sjOr2rmM52GzhpMHjDEE1kpQeRxwFDr4YcBEimi'
    }

    mobile_number = mobile_number or "8383909618"
    url = "https://cdndemo-api.co-vin.in/api/v2/auth/generateOTP"
    data = {
        'mobile': mobile_number
    }
    return requests.post(url, headers=headers, data=json.dumps(data))


def send_request_confirm_otp_protected_api(otp, txn_id):
    headers = {
        'Accept-Language': 'en_US',
        'User-Agent': '',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Api-Key': '3sjOr2rmM52GzhpMHjDEE1kpQeRxwFDr4YcBEimi'
    }

    url = "https://cdndemo-api.co-vin.in/api/v2/auth/confirmOTP"
    data = {
        'otp': otp,
        'txnId': txn_id
    }
    return requests.post(url, headers=headers, data=json.dumps(data))


def sent_request_to_register_beneficiary_protected_api():
    headers = {
        'Accept-Language': 'en_US',
        'User-Agent': '',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Api-Key': '3sjOr2rmM52GzhpMHjDEE1kpQeRxwFDr4YcBEimi'
    }
    url = "https://cdndemo-api.co-vin.in/api/v2/registration/beneficiary/new"
    data = {
        "name": "Apparao",
        "birth_year": "1980",
        "gender_id": 1,
        "photo_id_type": 1,
        "photo_id_number": "9999",
        "comorbidity_ind": "Y",
        "consent_version": "1"
    }
    return requests.post(url, headers=headers, data=json.dumps(data))
