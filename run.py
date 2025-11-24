#!/usr/bin/python
# -*- coding: utf-8 -*-
import streamlit.web.cli as stcli
import os, sys
import streamlit.components.v1 as components
from configparser import ConfigParser
from pathlib import Path
import streamlit as st
from io import BytesIO
from dify_client import DifyTestCaseGenerator
import xlsxwriter
import platform
import base64
import time
import re
from xmindparser import xmind_to_dict
import requests
import json
import time
from typing import Dict, Any, Optional




def resolve_path(path):
    resolved_path = os.path.abspath(os.path.join(os.getcwd(), path))
    return resolved_path


if __name__ == "__main__":
    sys.argv = [
        "streamlit",
        "run",
        resolve_path("page.py"),
        "--global.developmentMode=false",
    ]
    sys.exit(stcli.main())
