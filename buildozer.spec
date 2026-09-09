[app]
title = Dark Knight Chronicles
package.name = darkknight
package.domain = org.darkknight
version = 0.1

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas

requirements = python3,kivy
p4a.branch = master

orientation = landscape
fullscreen = 1

android.permissions = INTERNET
android.api = 33
android.minapi = 24
android.build_tools_version = 33.0.0

[buildozer]
log_level = 2
build_dir = .buildozer
bin_dir = bin
