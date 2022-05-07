Setting Up your Google Cloud Project
====================================

Overview
--------

.. contents::

This document will take you through the steps needed to set up a Google Cloud
project to make use of this tool.

Most information was taken from `this Linux Uprising post`_ and then modified
based on new findings.

Each step here assumes that you're logged into your Google account.

.. note::

   The steps outlined here are correct as of 2021-06-06. The author makes no
   attempt to keep up-to-date with the latest changes to the Google Cloud web
   interface or settings.


Create the Google Cloud Project
-------------------------------

#. Head to https://console.cloud.google.com/cloud-resource-manager?pli=1

   * If you don't yet have any Google Cloud projects, select your country
     and agree the to the Terms of Service.

#. Press **Create Project**.
#. Enter a project name. For example, "Photos Sync". This name must be unique
   within your account and cannot be changed in the future.
#. Leave **Location** as the default "No Organization".
#. Press Create.


Enable the Photos API
---------------------

#. Ensure that the project you made above is the active project.
#. Click on the top-left hamburger menu and find **APIs & Services** > **Library**.
#. Search for the **Photos Library API** by Google.
#. Enable it.


Configure OAuth Consent
-----------------------

#. Find **APIs & Services** > **OAuth consent screen**
#. Set **User Type** to External.
#. Press Create
#. App Registration - OAuth consent screen:

   #. Set your **App Name**. For example, "Photos Sync". Note that this does
      **not** have to be the same as the project name. Do not include "Google"
      in the name or this will fail.
   #. Enter your email address as the **User support email**.
   #. Enter your email address as the **Developer contact information**.
   #. Add other fields as desired (they can be left blank).
   #. Press **Save and Continue**.

#. App Registration - Scopes

   #. Nothing is *needed* here - you can just ignore everything and press
      **Save and Continue**.
#. App Registration - Test Users:

   #. Add your email address as a test user.
   #. Press **Save and Continue**.

#. App Registration - Optional Info:

   #. Nothing is required here, add things if you want.
   #. Press **Save and Continue**.

#. Review the summary and press **Back to Dashboard**.


Create the OAuth Credentials
----------------------------

#. Find **APIs & Services** > **Credentials**
#. Press **+ Create Credentials** and select **OAuth client ID**.
#. Application Type: Desktop App
#. Name: "Photos Sync OAuth Client"
#. Save the Client ID and the Secret in your password manager.
#. Download the OAuth client ID as JSON and save it as ``client_secret.json``.


Publish the App
---------------

.. important::

   Failure to publish the app will result in your auth token expiring after
   **7 days**. See `the Google Cloud docs`_ and `Issue #290`_ for details.

#. Head to **APIs & Services** > **OAuth consent screen**
#. Press **Publish App**.
#. Read the notice and press **Confirm**.


At this point you should be able to run ``gphotos-sync`` using the instructions
found in the README_.


.. _`this Linux Uprising post`: https://www.linuxuprising.com/2019/06/how-to-backup-google-photos-to-your.html
.. _`the Google Cloud docs`: https://developers.google.com/identity/protocols/oauth2#expiration
.. _`Issue #290`: https://github.com/gilesknap/gphotos-sync/issues/290
.. _README: ../README.rst
