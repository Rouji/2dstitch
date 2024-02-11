from setuptools import setup

setup(
    name = "2dstitch",
    version = "0.1",
    description = ("2D Stitch"),
    url = "https://github.com/rouji/2dstitch",
    packages=['2dstitch'],
    install_requires=[
        'opencv-python',
        'numpy',
    ]
)
