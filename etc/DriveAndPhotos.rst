Google Photos and Google Drive Integration
==========================================

Introduction
------------
I am documenting here the idiosyncrasies of Drive and Photos integration. I am using Google's APIs to both of these services in order to backup my photos and metadata with gphotos-sync. This is necessary because of the first subject below 'Downloading Photos'.

For the purposes of this discussion, assume that these features are switched on:-

* *'Show Google Drive photos & videos in your Photos library'* at https://photos.google.com/settings
*  *'Create a Google Photos folder'* in settings at  https://drive.google.com/drive/my-drive

Downloading Photos
------------------
Google Drive has a nice, up to date, fully supported API. With this API it is possible to download all photos every uploaded to Google Photos. However, unbelievably, edits to photos in Google Photos are not reflected in their Drive copies and vice versa. If you edit in either service then those edited items diverge. In contrast, deleting entries from one service does delete in the other as well.

So the best thing to do is only use Google Photos then? Well no, you currently have to use the deprecated Picasaweb API for this.

Picasaweb can only access photos which are included in albums. There is a mechanism for listing recent photos but this seems to top out at around 800 photos.

There is also a 'Auto Upload' album which contains all photos ever uploaded. However the API blows up at the 10,000 photo mark.

Thus I chose to use:

- Drive for downloading photos
- Picasaweb for getting information about the albums in Google Photos.
- Look for files that have been modified in picasaweb and also download those
- Create a set of folders with soft links to represent albums and point at the picasaweb downloaded files in the case where they are newer than their drive counterparts

This approach has the following limitations:

* Photos modified in Google Photos which are not in an album and also not in the last 10,000 photos uploaded will have their modifications lost in the backup
* To implement this, a mechanism for matching the photos listed in picasaweb and drive is required. Including the ability to tell which was edited most recently


Creations
-------------
Google Photos own creations such as Panoramas and Movies etc. Are not know to drive and hence any older than 10000 most recent items (and not in an album) simply cannot be accessed programatically. A workaround to this is to create a folder and drop them all in (as long as you have less than 10000, in which case they would need multiple albums)

Modified Date
-------------
Modify date reflects the time that files were imported into the service.

When photos are imported into Google Photos they appear at some point later in Google Drive. This can be some time later. Maybe 10s of minutes if you upload many simultaneously. In fact it seems that some may not appear until you browse them in Google photos, or perhaps some may never appear.

Even if they do appear then the modify dates of Drive and Photos instances of these files do not match and may vary from a few minutes to days.

This would be fine if the modify dates in Drive was always later than Photos but this is not the case. In a recent experiment I uploaded 10 files and their modify dates in Photos spanned 5 minutes. The modify times on Drive spanned 35 minutes and overlapped the Photos times in both directions.

It looks like some of my uploads in my test account have very old modify dates in Drive (like 2 years old). All my test photos are my own from my main account and I can only guess that drive has linked to existing entries (by hash) across accounts.

Conclusion - use of modified date in Drive vs Picasweb is not viable.



