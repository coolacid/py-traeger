from setuptools import setup

setup(
    name='treagerwifire',
    version='1.0.0',
    description='Access and interact with Treager WiFire',
    packages=['traeger'],
    include_package_data=True,
    scripts=['bin/traeger-wifire'],
    install_requires=[
        'paho-mqtt==1.6.1',
        'boto3==1.24.7',
        'dacite==1.6.0',
    ]
)
