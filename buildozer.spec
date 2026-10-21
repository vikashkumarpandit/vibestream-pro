[app]
title = VibeStream Pro
package.name = vibestream
package.domain = org.vibestream
source.include_exts = py,png,jpg,kv,atlas
source.include_patterns = assets/*
version = 1.0
requirements = python3,kivy,flask,requests,urllib3,certifi,idna,charset-normalizer,yt-dlp
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
