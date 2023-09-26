from setuptools import setup

setup(
    name="ansible-mock",
    version="0.1",
    description="Test ansible roles on the fly with LXD",
    author="Nathan Hensel",
    packages=["ansible_mock"],
    install_requires=["pylxd"],
    entry_points={
        "console_scripts": [
            "ansible_mock = ansible_mock.main:main",
        ]
    },
)
