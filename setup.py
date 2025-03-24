from setuptools import find_packages, setup

from merge_tracks_with_video.metadata import __package_name__, __version__

setup(
    name=__package_name__,
    version=__version__,
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=[
        'chardet',
        'srt',
    ],
    entry_points={
        'console_scripts': [
            'merge-tracks-with-video = merge_tracks_with_video.main:main',
        ],
    },
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GPL 3.0',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',
)
