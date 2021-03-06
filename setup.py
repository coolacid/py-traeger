from setuptools import setup

setup(
    name='treagerwifire',
    version='1.0.0',
    description='Access and interact with Treager WiFire',
    packages=['traeger'],
    include_package_data=True,
    scripts=['bin/traeger-wifire'],
    install_requires=[
        'paho-mqtt>=1.6.0,<1.7.0',
        'boto3>=1.24.0,<1.25.0',
        'dacite>=1.6.0,<1.7.0',
    ]
)
