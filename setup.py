from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in bizmarketing/__init__.py
from bizmarketing import __version__ as version

setup(
	name="bizmarketing",
	version=version,
	description="Comprehensive Marketing Operations for Frappe",
	author="Biz Technology Solutions",
	author_email="hadi@biztechnology.et",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
