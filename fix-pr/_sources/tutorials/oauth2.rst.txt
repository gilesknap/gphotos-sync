.. _Client ID:

Creating an OAuth Client ID
===========================

Overview
--------

.. contents::

This document will take you through the steps needed to set up a Google Cloud
project and create an OAuth client ID for gphoto-sync.

For a discussion of the purpose of this ID see `Tokens`.

Each step here assumes that you're logged into a personal Google account.

.. note::
   The steps outlined here are correct as of May 2022. Their is quite a
   bit of churn in the Google Cloud Console UI so the screens may change a
   bit.


Create a Google Cloud Project
-----------------------------

#. Head to https://console.cloud.google.com

    * If you have not set up Google Cloud before, select your country
      and agree the to the Terms of Service.

    .. image:: oauth-images/0.png
        :align: center
        :scale: 100 %

#. In the top banner the currently selected project is shown. If you have
   no previous projects this will say 'Select a project'

   * Click on the current project name or 'Select a project'

   * This will bring up the 'Select a Project' dialog

    .. image:: oauth-images/1.png
        :align: center
        :scale: 100

#. Press **New Project**.
#. Enter a project name. For example, "gphotos". This name must be unique
   within your account and cannot be changed in the future.
#. Leave **Location** as the default "No Organization".
#. Press Create.

    .. image:: oauth-images/2.png
        :align: center
        :scale: 100



Enable the Photos API
---------------------

#. Ensure that the project you made above is the active project.
#. Click on the top-left hamburger menu and find **APIs & Services** > **Library**.

    .. image:: oauth-images/3.png
        :align: center
        :scale: 75

#. Search for the **Photos Library API** by Google and select it.
    .. image:: oauth-images/4.png
        :align: center
        :scale: 75

#. Enable it.

    .. image:: oauth-images/5.png
        :align: center
        :scale: 75

Configure OAuth Consent
-----------------------

#. Find **APIs & Services** > **OAuth consent screen**

    .. image:: oauth-images/6.png
        :align: center
        :scale: 75

#. Set **User Type** to External.
#. Press Create

    .. image:: oauth-images/7-oauth_concent.png
        :align: center
        :scale: 75

#. App Registration - OAuth consent screen:

   #. Set your **App Name**. For example, "gphotos". Note that this does
      **not** have to be the same as the project name. Do not include "Google"
      in the name or this will fail.
   #. Enter your email address as the **User support email**.
   #. Enter your email address as the **Developer contact information**.
   #. Leave all other fields.
   #. Press **Save and Continue**.

    .. image:: oauth-images/8-app_registration.png
        :align: center
        :scale: 75

#. App Registration - Scopes

   #. Nothing is *needed* here - you can just ignore everything and press
      **Save and Continue**.

    .. image:: oauth-images/9-scopes.png
        :align: center
        :scale: 75

#. App Registration - Test Users:

   #. Nothing needed here as you are going to publish the project. This means
      it will no longer be in the testing state.
   #. Press **Save and Continue**.

    .. image:: oauth-images/10-test_users.png
        :align: center
        :scale: 75

#. Summary

    #. You will now see a summary screen like this
    #. Review the summary and press **Back to Dashboard**.

    .. image:: oauth-images/11-summary.png
        :align: center
        :scale: 75


Create the OAuth Credentials
----------------------------

#. Find **APIs & Services** > **Credentials**
#. Press **+ Create Credentials** and select **OAuth client ID**.


    .. image:: oauth-images/12-create_creds.png
        :align: center
        :scale: 75

#. Choose Desktop App
    #. Choose name for your credentials e.g. gphotos
    #. Click **Create**

    .. image:: oauth-images/14-create_id.png
        :align: center
        :scale: 75

#. Click **Download JSON** to download the OAuth client ID as JSON and
   save it as ``client_secret.json``.

    .. image:: oauth-images/15-created.png
        :align: center
        :scale: 75


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

.. _`the Google Cloud docs`: https://developers.google.com/identity/protocols/oauth2#expiration
.. _`Issue #290`: https://github.com/gilesknap/gphotos-sync/issues/290
.. _README: https://github.com/gilesknap/gphotos-sync/blob/main/README.rst


Move client_secret.json
-----------------------

    #. The client_secret.json must be moved to the correct location
    #. Each supported operating system has a different location where it will
       look for this file.
    #. Return the `Tutorial` for details of where to put this file.