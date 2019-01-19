#!/usr/bin/env python3
# coding: utf-8

import configparser
import distutils
import os
import shutil
import subprocess
import sys

import setuptools


class build_js(setuptools.Command):

    description = 'install JS dependencies using yarn or npm'
    user_options = [
        ('vendor-dir', None, 'path to the vendor directory'),
        ('packages', 'p', 'packages to install'),
    ]

    def initialize_options(self):
        """Set default values for options."""
        self._cfg = configparser.ConfigParser(defaults={
            'vendor-dir': 'ext',
            'packages': ''
        })
        self._cfg.read(self.distribution.find_config_files())
        self.vendor_dir = self._cfg.get('build_js', 'vendor-dir')
        self.packages = self._cfg.get('build_js', 'packages')

    def finalize_options(self):
        """Post-process options."""
        if self.packages is not None:
            packages = self.packages.strip()
            sep = max('\n,;', key=packages.count)
            self.packages = list(map(str.strip, packages.split(sep)))

    def has_command(self, cmd):
        return subprocess.check_call([cmd, "--version"], stdout=subprocess.PIPE) == 0

    def run(self):
        """Run command."""
        if self.packages:
            shutil.rmtree(self.vendor_dir)
            if self.has_command("yarn"):
                shutil.rmtree('yarn.lock', ignore_errors=True)
                shutil.rmtree('package.json', ignore_errors=True)
                cmd = ["yarn", "add", "--modules-folder", self.vendor_dir] + self.packages
                self.announce(f'running {" ".join(cmd)!r}', level=distutils.log.INFO)
                subprocess.call(cmd)
            elif self.has_command('npm'):
                cmd = ['npm', 'install'] + self.packages
                self.announce(f'running {" ".join(cmd)!r}', level=distutils.log.INFO)
                subprocess.call(cmd)
                os.rename('node_modules', self.vendor_dir)



class run(setuptools.Command):

    description = 'launch the website'
    user_options = [
        ('vendor-dir', None, 'path to the vendor directory'),
        ('img-dir', None, 'path to the images directory')
    ]

    def initialize_options(self):
        self._cfg = configparser.ConfigParser(default_section='run', defaults={
            'vendor-dir': 'ext',
            'img-dir': os.path.join('static', 'img')
        })
        self._cfg.read(self.distribution.find_config_files())
        self.vendor_dir = self._cfg.get('run', 'vendor-dir')
        self.img_dir = self._cfg.get('run', 'img-dir')

    def finalize_options(self):
        self.vendor_dir = os.path.abspath(self.vendor_dir)
        self.img_dir = os.path.abspath(self.img_dir)
        if not os.path.isdir(self.vendor_dir):
            self.announce(f'directory {self.vendor_dir} does not exist', level=distutils.log.FATAL)
        if not os.path.isdir(self.img_dir):
            self.announce(f'directory {self.img_dir} does not exist', level=distutils.log.FATAL)

    def run(self):
        import cherrypy
        import botrytis.server
        cherrypy.quickstart(
            botrytis.server.BotrytisWebsite(),
            "/",
            {
                "/static": {
                    "tools.staticdir.on": True,
                    "tools.staticdir.dir": self.vendor_dir,
                },
                "/static/img": {
                    "tools.staticdir.on": True,
                    "tools.staticdir.dir": self.img_dir
                },
            }
        )




if __name__ == "__main__":
    setuptools.setup(
        cmdclass={
            "build_js": build_js,
            "run": run,
        }
    )
