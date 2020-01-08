from setuptools import setup, find_packages
import lasto3dtiles

setup(
    name='lasto3dtiles',
    version='0.0.1',
    packages=[
        'lasto3dtiles',
        'lasto3dtiles.format',
        'lasto3dtiles.task',
        'lasto3dtiles.util',
    ],
    install_requires=[
        'cython',
        'scipy',
        'laspy',
        'luigi',
        'matplotlib',
        'numpy',
        'pandas',
        'pillow',
        'pymap3d',
        'open3d',
        'requests',
        'transforms3d',
    ],
    entry_points={
        'console_scripts': [
            'lasto3dtiles = lasto3dtiles.command:command',
        ],
    },
)
