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

class RobotCfg(object):
	def	__init__(self):
		curpath = os.path.dirname(os.path.abspath(__file__))
		cfgpath = os.path.split(curpath)[0] + "\\cfg\\dinos.cfg"
		cfg = ConfigParser.RawConfigParser()
		cfg.optionxform = str
		cfg.read(cfgpath)
		self.ProjectName = cfg.get("automation", "ProjectName")
		self.description = cfg.get("automation", "description")
		self.TestPath = cfg.get("automation", "TestPath")
		self.RobotPath = cfg.get("automation", "RobotPath")
		self.RobotHeader = cfg.get("automation","RobotHeader").split(",")
		self.ModuleVars = cfg.get("automation","ModuleVars").split(",")
		self.DataVars = cfg.get("automation","DataVars").split(",")
		

robotCfg = RobotCfg()		
		
		
		