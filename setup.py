from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in masar_hrms/__init__.py
from masar_hrms import __version__ as version

setup(
	name="masar_hrms",
	version=version,
	description="Masar Hrms",
	author="KCSC",
	author_email="info@kcsc.com.jo",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
