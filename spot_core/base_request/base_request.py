#!/usr/bin/python
# -*- coding:utf-8 -*-

import json
import requests
import hmac
import hashlib
import base64
import time
from uuid import uuid1
from urllib.parse import urljoin
import socket

from requests import Session

try:
    import pkg_resources

    version = 'v' + pkg_resources.get_distribution("kucoin-python").version
except (ModuleNotFoundError, pkg_resources.DistributionNotFound):
    version = 'v1.0.0'


class KucoinBaseRestApi(object):


    def __init__(self, key='', secret='', passphrase='', url='', is_v1api=False):
        """
        https://docs.kucoin.com

        :param key: Api Token Id  (Mandatory)
        :type key: string
        :param secret: Api Secret  (Mandatory)
        :type secret: string
        :param passphrase: Api Passphrase used to create API  (Mandatory)
        :type passphrase: string
        """

        if url:
            self.url = url
        else:
            self.url = 'https://api.kucoin.com'

        self.key = key
        self.secret = secret
        self.passphrase = passphrase
        self.is_v1api = is_v1api
        self.TCP_NODELAY = 0
        self._session = None

    @property
    def session(self) -> Session:
        return self._session
    @session.setter
    def session(self, session: Session):
        self._session = session

    def _request(self, method, uri, timeout=5, auth=True, params=None):
        uri_path = uri
        data_json = ''
        if method in ['GET', 'DELETE']:
            if params:
                strl = []
                for key in sorted(params):
                    strl.append("{}={}".format(key, params[key]))
                data_json += '&'.join(strl)
                uri += '?' + data_json
                uri_path = uri
        else:
            if params:
                data_json = json.dumps(params)

                uri_path = uri + data_json

        headers = {}
        if auth:
            now_time = int(time.time()) * 1000
            str_to_sign = str(now_time) + method + uri_path
            sign = base64.b64encode(
                hmac.new(self.secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
            if self.is_v1api:
                headers = {
                    "KC-API-SIGN": sign,
                    "KC-API-TIMESTAMP": str(now_time),
                    "KC-API-KEY": self.key,
                    "KC-API-PASSPHRASE": self.passphrase,
                    "Content-Type": "application/json"
                }
            else:
                passphrase = base64.b64encode(
                    hmac.new(self.secret.encode('utf-8'), self.passphrase.encode('utf-8'), hashlib.sha256).digest())
                headers = {
                    "KC-API-SIGN": sign,
                    "KC-API-TIMESTAMP": str(now_time),
                    "KC-API-KEY": self.key,
                    "KC-API-PASSPHRASE": passphrase,
                    "Content-Type": "application/json",
                    "KC-API-KEY-VERSION": "2"
                }
        headers["User-Agent"] = "kucoin-python-sdk/" + version
        url = urljoin(self.url, uri)
        if not self.session:
            self.session = requests.Session()
            if self.TCP_NODELAY == 1:
                adapter = requests.adapters.HTTPAdapter()
                adapter.socket_options = [
                    (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                ]
                self.session.mount('https://', adapter)
        start_time = time.time_ns()
        if method in ['GET', 'DELETE']:
            response_data = self.session.request(method, url, headers=headers, timeout=timeout)
        else:
            response_data = self.session.request(method, url, headers=headers, data=data_json,
                                                 timeout=timeout)
        end_time = time.time_ns()
        
        return self.check_response_data(response_data, start_time, end_time)

    @staticmethod
    def check_response_data(response_data, start_time = 0, end_time = 0):
        if response_data.status_code == 200:
    
            # Get the server time consumed
            headers = response_data.headers
            x_in_time = headers.get("x-in-time")
            x_out_time = headers.get("x-out-time")
            server_sttime = 0
            server_edtime = 0
            if x_in_time:
                parts = x_in_time.split(';')
                for part in parts:
                    key_value = part.split('-')
                    if len(key_value) == 2:
                        key, value = key_value
                        if key == '5':
                            server_sttime = int(value)
                            break
            if x_out_time:
                key_value = x_out_time.split('-')
                if len(key_value) == 2:
                    key, value = key_value
                    server_edtime = int(value)

            try:
                data = response_data.json()
            except ValueError:
                raise Exception("Invalid JSON response")
            else:
                if data and data.get('code'):
                    if data.get('code') == '200000':
                        if data.get('data') and isinstance(data['data'], int) == False:
                            data['data']['sttime'] = start_time / 1000000
                            data['data']['edtime'] = end_time / 1000000
                            data['data']['srvsttime'] = server_sttime / 1000
                            data['data']['srvedtime'] = server_edtime / 1000
                            return data['data']
                        else:
                            data['sttime'] = start_time / 1000000
                            data['edtime'] = end_time / 1000000
                            data['srvsttime'] = server_sttime / 1000
                            data['srvedtime'] = server_edtime / 1000
                            return data
                    else:
                        error_msg = data.get('msg', 'Unknown error')
                        raise Exception(f"API Error {data.get('code')}: {error_msg}")
        else:
            error_msg = response_data.text
            raise Exception(f"HTTP Error {response_data.status_code}: {error_msg}")

    @property
    def return_unique_id(self):
        return ''.join([each for each in str(uuid1()).split('-')])
