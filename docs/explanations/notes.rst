Why is Google Photos Sync Read Only
===================================

Google Photos Sync is a backup tool only. It never makes any changes to your
Google Photos Library in the cloud. There are two primary reasons for this:

- The Photos API provided by Google is far too restricted to make changes 
  in any meaningful way. For example

  - there is no delete function
  - you cannot add photos to an album unless it was created by the same
    application that is trying to add photos

- Even if the API allowed it, this would be a very hard problem, because
  it is often hard to identify if a local photo or video matches one in the 
  cloud. Besides this, I would not want the resposibility of potentially 
  trashing someone's photo collection. 
