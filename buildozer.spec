[app]
title = Dark Knight Chronicles
package.name = darkknight
package.domain = org.darkknight

# TAMBAHKAN BARIS INI:
version = 0.1

source.dir = .
source.include_exts = py,png,jpg,kv,atlas
requirements = python3,kivy
orientation = landscape
android.permissions = INTERNET
android.api = 33
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True

[buildozer]
log_level = 2
build_dir = .buildozer
bin_dir = bin

