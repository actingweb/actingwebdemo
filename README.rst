===============
Getting Started
===============

This ActingWeb library is inself a fully working app that can be deployed
to Google AppEngine.

It does not really use anything AppEngine specific beyond the database (ndb),
so it can easily be ported to e.g. running in a Docker container. The
deployment is then a bit more complex as you need a database container as well.
Building this into the current python library as an option is a TODO.

Google AppEngine
----------------

1. Go to https://cloud.google.com/appengine, and log in using your google account.
You can go to https://cloud.google.com/appengine/docs to get access to the quick
start, however, the tutorial I recommend is here. It covers a lot things in a
guestbook app you don’t really need to understand to get started, but it’s a
simple way to deploy your first app. If you plan to re-use your test app,
take care when choosing an app name as it cannot be changed and will be part of the
app URL.

2. Once you have deployed your first python 2.7 app, you can either just re-use
that app (and replace the code) or create a new project at
https://console.cloud.google.com.  You then add the app with the same name
in Google AppEngineLauncher on your computer and a new local directory will be
created for you. Also remember, you will need the public URL created for your
Appengine App in the next step.

3. Copy the acting-web-gae-library code into your app directory and edit appl.yaml.
The first line must be edited to your app name

4. Deploy the app to Google AppEngine and you should get a sign-up form when you go
to the URL of the app!

Use the library for your own projects
-------------------------------------

For how to use and extend the library, you can have a look at an example where
the ActingWeb library is used for Cisco Spark, the free collaboration service:
http://stuff.ttwedel.no/latest-armyknife-code-html
