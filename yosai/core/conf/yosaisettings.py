"""
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
"""

"""
Following are the settings and configuration for Yosai.

Yosai follows a custom-else-default method of obtaining configuration
settings: First, it obtains customized, user-specied configuration.  Any
other required configuration attributes that are unavailable through customized
configuration are obtained by (global) default settings.

This design is inspired by, or a copy of, source code written for Django.
"""
import logging
from pathlib import Path
import yaml
import os
from yosai.core import (
    FileNotFoundException,
    MisconfiguredException,
)

ENV_VAR = "YOSAI_CORE_SETTINGS"
empty = object()
logger = logging.getLogger(__name__)


class LazySettings:
    """
    LazyConfig proxies the custom-else-default settings configuration process.
    Required settings that are not user-defined (custom) will default to those
    specified in default settings.
    """

    def __init__(self, env_var):
        self._wrapped = empty
        self.__dict__["env_var"] = env_var

    def __getattr__(self, name):
        if self._wrapped is empty:
            self._setup(name)
        return getattr(self._wrapped, name, None)

    def __setattr__(self, name, value):
        if name == "_wrapped":
            # Assign to __dict__ to avoid infinite __setattr__ loops.
            self.__dict__["_wrapped"] = value
        else:
            if self._wrapped is empty:
                self._setup()
            setattr(self._wrapped, name, value)

    def __delattr__(self, name):
        if name == "_wrapped":
            raise TypeError("can't delete _wrapped.")
        if self._wrapped is empty:
            self._setup()
        delattr(self._wrapped, name)

    @property
    def configured(self):
        return self._wrapped is not empty

    def _setup(self, name=None):
        """
        Load the settings module referenced by env_var. This environment-
        defined configuration process is called during the settings
        configuration process.
        """
        envvar = self.__dict__['env_var']
        settings_file = os.environ.get(envvar)
        if not settings_file:
            msg = ("Requested settings, but none can be obtained for the envvar."
                   "Since no config filepath can be obtained, a default config "
                   "will be used.")
            logger.warning(msg)
            settings_file = "yosai_settings.yaml"

        self._wrapped = Settings(settings_file)


class Settings:

    def __init__(self, settings_filepath):
        self.load_config(settings_filepath)

    def get_config(self, filepath):
        if os.path.exists(filepath):

            with Path(filepath).open() as stream:
                config = yaml.load(stream)

        else:
            raise FileNotFoundException('could not locate: ' + str(filepath))
        return config

    def load_config(self, filepath):
        try:
            config = self.get_config(filepath)
            tempdict = {}
            tempdict.update(self.__dict__)
            tempdict.update(config)
            self.__dict__ = tempdict
        except (TypeError, ValueError):
            raise MisconfiguredException('Settings failed to load attrs')


settings = LazySettings(ENV_VAR)
