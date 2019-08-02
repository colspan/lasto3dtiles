from setuptools import setup, find_packages
import lasto3dtiles

setup(
    name='lasto3dtiles',
    version='0.0.1',
    packages=[
        'lasto3dtiles',
        'lasto3dtiles.format',
        'lasto3dtiles.task',
    ],
    entry_points={
        'console_scripts': [
            'lasto3dtiles = lasto3dtiles.command:command',
        ],
    },
)
