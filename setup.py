import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tensorwatch",
    version="0.3.2",
    author="Shital Shah",
    author_email="shitals@microsoft.com",
    description="Interactive Realtime Debugging and Visualization for AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sytelus/tensorwatch",
    packages=setuptools.find_packages(),
	license='MIT',
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    install_requires=[
          'dill', 'matplotlib', 'numpy', 'pyzmq', 'plotly', 'receptivefield', 'torchstat'
    ]
)