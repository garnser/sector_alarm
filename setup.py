from setuptools import setup, find_packages

setup(
    name='sectoralarm',
    version='1.1.1',
    packages=find_packages(),
    install_requires=[
        'requests',
    ],
    author='Jonathan Petersson',
    author_email='jpetersson@garnser.se',
    description='A Python library for interacting with the Sector Alarm API.',
    url='https://github.com/garnser/sector_alarm',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
