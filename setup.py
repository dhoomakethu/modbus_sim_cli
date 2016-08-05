"""
Copyright (c) 2016 Riptide IO, Inc. All Rights Reserved.
"""

from setuptools import setup, find_packages
from setuptools.command.install import install
from modbus_sim import __version__

packages = find_packages()
with open('requirements') as reqs:
    install_requires = [
        line for line in reqs.read().split('\n')
        if (line and not line.startswith('--'))
    ]
long_description = None
with (open('README.md')) as readme:
    long_description = readme.read()


def _copy_configs():
    """
    copies device config from site-packages to home directory
    :return:
    """
    import os
    home_dir = os.path.expanduser("~")
    simu_dir = os.path.join(home_dir, "modbus_sim")

    try:
        import modbus_sim
        import shutil
        install_dir = modbus_sim.__path__[0]

        print("**********************************************************")

        print("Home directory: %s" % home_dir)
        print("modbus_simu_cli package "
                  "installed directory: %s" % install_dir)
        print("modbus_simu config directory: %s" % simu_dir)
        print("**********************************************************")
        if os.path.exists(simu_dir):
            shutil.rmtree(simu_dir)
        copy = ["configs"]
        print("copying '%s'" % simu_dir)
        for d in copy:
            shutil.copytree(
                os.path.join(install_dir, d),
                os.path.join(simu_dir, d),
                ignore=shutil.ignore_patterns("*.pyc")
            )
            shutil.rmtree(os.path.join(install_dir, d))

    except ImportError:
        print("modbus_simu package not installed!!")

    print("done!!")


class ModbusSimuInstaller(install):
    def run(self):
        install.run(self)
        self.execute(_copy_configs, (), msg="Running Post Install scripts")


setup(name="modbus_simu",
      url='https://github.com/dhoomakethu/modbus_sim_cli',
      version=__version__,
      packages=packages,
      cmdclass={'install': ModbusSimuInstaller},
      description="Modbus TCP/RTU device simulator",
      long_description=long_description,
      author="riptideio",
      install_requires=install_requires,
      scripts=['modbus_sim/scripts/modbus_simulator'],
      include_package_data=True,

      )
