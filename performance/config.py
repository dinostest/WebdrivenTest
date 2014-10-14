#  Copyright Xiang Liu (liu980299@gmail.com)
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import ConfigParser,os

class PerformanceCfg(object):
	def	__init__(self):
		curpath = os.path.dirname(os.path.abspath(__file__))
		cfgpath = os.path.split(curpath)[0] + "\\cfg\\dinos.cfg"
		cfg = ConfigParser.RawConfigParser()
		cfg.optionxform = str
		cfg.read(cfgpath)
		self.ProjectName = cfg.get("performance", "ProjectName")
		self.TestPath = cfg.get("performance", "TestPath")
		self.JMeterPath = cfg.get("performance", "JMeterPath")
		self.JMeterHeader = cfg.get("performance","JMeterHeader").split(",")
		self.ReportHeader = cfg.get("performance","ReportHeader").split(",")
		self.ModuleVars = cfg.get("performance","ModuleVars").split(",")
		self.DataVars = cfg.get("performance","DataVars").split(",")

perfCfg = PerformanceCfg()		
		
		
		