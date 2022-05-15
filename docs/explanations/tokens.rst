.. _Tokens:

Google OAuth Tokens for gphotos-sync
====================================

Introduction
------------

There are two kinds of authentication required to run gphotos-sync.

  - First the application must authenticate with Google to authorize the use
    of the Google Photos API. This gives it permission to perform the 
    second authentication step.
  - Second, an individual User Account must me authenticated to allow access
    to that user's Google Photos Library.

The secret information that enables these authentication steps is held in 
two files:

  - client_secret.json holds the OAuth application ID that allows the 
    first step. This is stored in an application configuration folder.
    There is only one of these files per installation of gphotos-sync.
    See `Client ID` for details of creating this file.
  - .gphotos.token holds the user token for each user you are backing up 
    photos for. This resides in the root folder of the library backup.
    See `Login` for details of creating this file.

Why Do We Need Client ID ?
--------------------------

The expected use of the client ID is that a vendor provides a single ID
for their application, Google verifies the application and then anyone 
can use it.

In this scenario ALL Google API calls would count against the vendor's
account. They would be charged for use of those APIs and they would
need to charge their users to make this worthwhile.

If I was to provide my own client ID with gphotos-sync then I would need
to charge a subscription to cover API costs.

Since this is FOSS I ask every user to create their own client ID
so they can take advantage of the free tier of Google API use that is 
available to every user.

Most normal use of gphotos-sync does not exceed the free tier. If it does
you will not be charged. The code is supposed to throttle back and go slower
to drop back into the free usage rate. However there is an issue with this 
feature at present and you will likely see an error:

    ``429 Client Error: Too Many Requests for url``. 

See https://github.com/gilesknap/gphotos-sync/issues/320,
https://github.com/gilesknap/gphotos-sync/issues/202 for details and 
workarounds.
