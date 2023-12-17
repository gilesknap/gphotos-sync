Known Issues
============


Known Issues with Google API
----------------------------
A few outstanding limitations of the Google API restrict what can be achieved. 
All these issues have been reported to Google and this project will be updated 
once they are resolved.

Unfortunately, a number of quite significant issues have remained unfixed for 
several years. I'm starting a discussion group in this repo for people to
discuss workarounds, and collect reports of how these things are affecting 
users. I intend to link this discussion group in the Google issue trackers
to see if it will encourage some response from Google.

To join the discussion go here 
https://github.com/gilesknap/gphotos-sync/discussions.

Pending API Issues
~~~~~~~~~~~~~~~~~~

-   There is no way to discover modified date of library media items. Currently 
    ``gphotos-sync`` will refresh your local copy with any new photos added since 
    the last scan but will not update any photos that have been modified in 
    Google Photos.

    - https://issuetracker.google.com/issues/122737849.


-   GOOGLE WON'T FIX. The API strips GPS data from images.

    - https://issuetracker.google.com/issues/80379228.

-   Video download transcodes the videos even if you ask for the original file 
    (=vd parameter). My experience is that the result is looks similar to the original
    but the compression is more clearly visible. It is a smaller file with 
    approximately 60% bitrate (same resolution).

    - https://issuetracker.google.com/issues/80149160

-   Photo download compresses the photos even if you ask for the original file 
    (=d parameter). This is similar to the above issue, except in my experience 
    is is nearly impossible to notice a loss in quality. It
    is a file compressed to approximately 60% of the original size (same resolution).

    - https://issuetracker.google.com/issues/112096115

-   Burst shots are not supported. You will only see the first file of a burst shot.

    - https://issuetracker.google.com/issues/124656564

Fixed API Issues
~~~~~~~~~~~~~~~~
-   FIXED BY GOOGLE. Some types of video will not download using the new API.

    - https://issuetracker.google.com/issues/116842164.
    - https://issuetracker.google.com/issues/141255600

Other Issues
------------
- Some mounted filesystems including NFS, CIFS and AFP do not support file locks 
  and database access will fail on them.

  - To fix, use the parameter --db-path to specify a location for your DB on 
    the local disk. This will perform better anyway.

GPS workaround
--------------
For a workaround to the GPS issue described below see this project  
https://github.com/DennyWeinberg/manager-for-google-photos