from setuptools import setup, find_packages

setup(
    name='TSBackEnd',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[
        'Flask==0.12.2',
        'Flask-SQLAlchemy==2.3.2',
        'python-dateutil==2.7.1'
    ]
)
