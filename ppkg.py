#!/usr/bin/env python

import os
import subprocess
import urlparse
import sys
import json


def copy_file(src_path, dst_path):
	with open(src_path, "r") as r:
		with open(dst_path, "w") as w:
			w.write(r.read())


def copy_files(src_path, dst_path):
	src_sub_dirs = os.listdir(src_path)
	
	for sub_dir_item in src_sub_dirs:
		src_file_entry = os.path.join(src_path, sub_dir_item)
		dst_file_entry = os.path.join(dst_path, sub_dir_item)
		if os.path.isdir(src_file_entry):
			if not os.path.exists(dst_file_entry):
				os.makedirs(dst_file_entry)
			copy_files(src_file_entry, dst_file_entry)
		else:
			copy_file(src_file_entry, dst_file_entry)


class Git(object):
	def __init__(self, git_repo, cache_path):
		self.repo = git_repo
		self.cache_path = cache_path
		self.git_cmd = ['git']
		self.repo_name = ""
		self.is_pull_action = False
		
		self.cwd = os.path.abspath(os.path.curdir)
		
		self._init()
		
	def _init(self):
		if not os.path.exists(self.cache_path):
			os.makedirs(self.cache_path)
			
		p = urlparse.urlparse(self.repo)
		repo_name = os.path.basename(p.path).split(".")[0]
		self.repo_name = repo_name
		
		full_repo_cache_path = os.path.join(self.cache_path, repo_name)

		if os.path.exists(full_repo_cache_path):
			self.git_cmd.append("pull")
			self.is_pull_action = True
		else:
			self.git_cmd.append("clone")
			self.git_cmd.append(self.repo)
		
	def download(self):
		dst_cache_path = self.cache_path
		if self.is_pull_action:
			dst_cache_path = os.path.join(dst_cache_path, self.repo_name)
		
		os.chdir(dst_cache_path)
		
		subprocess.call(self.git_cmd)
		
		os.chdir(self.cwd)
		
	def get_libdir(self, lib_name):
		return os.path.join(self.cache_path, self.repo_name, lib_name)
		
		
class Npm(object):
	def __init__(self, dst_dir):
		self.dst_dir = dst_dir
		self.cwd = os.path.abspath(os.path.curdir)
		
	def install(self):
		os.chdir(self.dst_dir)
		
		subprocess.call(["npm" if os.name == "posix" else "npm.cmd", "install"])
		
		os.chdir(self.cwd)
		
		
def load_config():
	"""
		ppkg.json
		{
			"project_path": "sources",
			"repo_cache": "_SDK",
			"repo": "https://git.oschina.net/himarvel/sdk.git",
			"projects": {
				"website": [
					"restful-client",
					"restful-server"
				]
			}
		}
	"""
	config = {}
	
	try:
		with open('ppkg.json', 'r') as f:
			config = json.load(f)
	except:
		pass
		
	return config
	
	
def copy_sdk_to_project(sdk_cache_path, project_modules_path):
	if not os.path.exists(project_modules_path):
		os.makedirs(project_modules_path)
	
	copy_files(sdk_cache_path, project_modules_path)
	
	
def init_project_modules_dir(project_root):
	if os.path.exists(project_root):
		return
	
	os.mkdir(os.path.join(project_root, "node_modules"))
	

def install_pkg():
	config = load_config()
	
	project_path = os.path.abspath(config["project_path"])
	repo_cache= config["repo_cache"]
	repo = config["repo"]
	projects = config["projects"]
	
	# clone or update sdk
	git = Git(repo, os.path.abspath(repo_cache))
	git.download()
	
	for prj_name, prj_deps in projects.items():
		init_project_modules_dir(os.path.join(project_path, prj_name))
		for dep in prj_deps:
			prj_modules_path = os.path.join(project_path, prj_name, "node_modules", dep)
			copy_sdk_to_project(git.get_libdir(dep), prj_modules_path)
			
			npm = Npm(prj_modules_path)
			npm.install()
			
	
def main(argv=sys.argv):
	print "Install package"

	install_pkg()
	
	print "Install package Success"
	
	return 0
	

if __name__ == "__main__":
	sys.exit(main())