from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in navari_hotel_addon/__init__.py
from navari_hotel_addon import __version__ as version

setup(
	name="navari_hotel_addon",
	version=version,
	description="Specific Funtionality for Hotel",
	author="Navari Limited",
	author_email="info@navari.co.ke",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
