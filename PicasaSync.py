#!/usr/bin/python
# coding: utf8
import gdata.gauth
import gdata.photos.service
from datetime import timedelta, datetime
import os.path
import glob
import urllib
from PicasaMedia import PicasaMedia
from DatabaseMedia import DatabaseMedia, MediaType
import Utils


# todo add removal local files for deleted picasa and album entries
# todo store album entry link files in the db for this purpose
# todo resurrect LocalData(GoogleData) in order to store link files in the db.
class PicasaSync(object):
    # noinspection SpellCheckingInspection
    PHOTOS_QUERY = '/data/feed/api/user/default/albumid/{0}'
    BLOCK_SIZE = 500
    ALBUM_MAX = 10000  # picasa web api gets 500 response after 10000 files
    HIDDEN_ALBUMS = ['Auto-Backup', 'Profile Photos']

    def __init__(self, credentials, root_folder, db):
        self._root_folder = root_folder
        self._db = db
        self._gdata_client = None
        self._credentials = credentials
        self._auth2token = gdata.gauth.OAuth2TokenFromCredentials(credentials)

        gd_client = gdata.photos.service.PhotosService()
        orig_request = gd_client.http_client.request
        gd_client = self._auth2token.authorize(gd_client)
        gd_client = Utils.patch_http_client(self._auth2token, gd_client,
                                            orig_request)
        gd_client.additional_headers = {
            'Authorization': 'Bearer %s' % self._credentials.access_token}
        self._gdata_client = gd_client

        # public members to be set after init
        self.startDate = None
        self.endDate = None
        self.album = None
        self.quiet = False
        self.includeVideo = False

    def match_drive_photo(self, media):
        file_keys = self._db.find_file_ids_dates(size=media.size)
        if file_keys and len(file_keys) == 1:
            return file_keys

        file_keys = self._db.find_file_ids_dates(filename=media.filename)
        if file_keys and len(file_keys) == 1:
            return file_keys

        if file_keys and len(file_keys) > 1:
            file_keys = self._db.find_file_ids_dates(filename=media.filename,
                                                     size=media.size)
            # multiple matches here represent the same image
            if file_keys:
                return file_keys[0:1]

        # search with date need to check for timezone slips due to camera not
        # set to correct timezone and missing or corrupted exif_date,
        # in which case revert to create date
        # ABOVE DONE
        # todo verify that the above is required in my photos collection
        for use_create_date in [False, True]:
            dated_file_keys = \
                self._db.find_file_ids_dates(filename=media.filename,
                                             exif_date=media.date,
                                             use_create=use_create_date)
            if dated_file_keys:
                print("MATCH ON DATE create %r %s, file: %s" %
                      (use_create_date, media.date, media.orig_name))
                return dated_file_keys
            for hour_offset in range(-12, 12):
                date_to_check = media.date + timedelta(hours=hour_offset)
                dated_file_keys = \
                    self._db.find_file_ids_dates(
                        filename=media.filename,
                        exif_date=date_to_check,
                        use_create=use_create_date)
                if dated_file_keys:
                    print(
                        "DATE MATCH date:{}, offset: {}, create:{}, "
                        "name:{}".format(
                            media.date, hour_offset, use_create_date,
                            media.orig_name))
                    return dated_file_keys
        # not found anything or found >1 result
        return file_keys

    def index_album_media(self, album_name=None, limit=None):
        print('\nIndexing Albums ...')
        albums = Utils.retry(10, self._gdata_client.GetUserFeed, limit=limit)

        total_photos = multiple = picasa_only = 0
        print('Album count %d\n' % len(albums.entry))

        for album in albums.entry:
            if album_name and album_name != album.title.text \
                    or album.title.text in self.HIDDEN_ALBUMS:
                continue

            total_photos += int(album.numphotos.text)

            # date filtering is crude at present - if I have changed
            # the title of an old album recently then a scan for recent files
            # would pick it up but its contents would be skipped in the drive
            # phase - I choose to leave this as is because:
            #   it is only problem for partially indexed photo stores
            #   the alternative is scanning all contents which is MUCH slower
            start_date = Utils.string_to_date(album.updated.text)
            if self.startDate:
                if Utils.string_to_date(self.startDate) > start_date:
                    continue
            if self.endDate:
                if Utils.string_to_date(self.endDate) < start_date:
                    continue

            if not self.quiet:
                print('  Album title: {}, number of photos: {}, date: {}'
                      .format(album.title.text, album.numphotos.text,
                              album.updated.text))

            # set initial end date to earliest possible
            end_date = datetime.min.replace(year=1900)
            album_id = album.gphoto_id.text
            # noinspection SpellCheckingInspection
            q = album.GetPhotosUri() + "&imgmax=d"

            start_entry = 1
            limit = PicasaSync.BLOCK_SIZE
            while True:
                photos = Utils.retry(10, self._gdata_client.GetFeed, q,
                                     limit=limit, start_index=start_entry)
                for photo in photos.entry:
                    media = PicasaMedia(None, self._root_folder, photo)
                    if (not self.includeVideo) and \
                            media.mime_type.startswith('video/'):
                        continue

                    # calling is_indexed to make sure duplicate_no is correct
                    # todo remove this when duplicate no handling is moved
                    media.is_indexed(self._db)
                    results = self.match_drive_photo(media)
                    if results and len(results) == 1:
                        # store link between album and drive file
                        (file_key, date) = results[0]
                        self._db.put_album_file(album_id, file_key)
                        file_date = Utils.string_to_date(date)
                        # make the album dates cover the range of its contents
                        if end_date < file_date:
                            end_date = file_date
                        if start_date > file_date:
                            start_date = file_date
                    elif results is None:
                        # no match so this exists only in picasa
                        picasa_only += 1
                        if self.includeVideo or not media.mime_type.startswith(
                                'video/'):
                            new_file_key = media.save_to_db(self._db)
                            self._db.put_album_file(album_id, new_file_key)

                            if not self.quiet:
                                print(u"Added {} {}".format(
                                    picasa_only, media.local_full_path))
                    else:
                        multiple += 1
                        print ('  WARNING multiple files match %s %s %s' %
                               (media.orig_name, media.date, media.size))

                # prepare offsets for the next block in next iteration
                start_entry += PicasaSync.BLOCK_SIZE
                if start_entry + PicasaSync.BLOCK_SIZE > PicasaSync.ALBUM_MAX:
                    limit = PicasaSync.ALBUM_MAX - start_entry
                    print ("LIMITING ALBUM TO 10000 entries")
                if limit == 0 or len(photos.entry) < limit:
                    break

            # write the album data down now we know the contents' date range
            self._db.put_album(album_id, album.title.text,
                               start_date, end_date)

        print('\nTotal Album Photos in Drive %d, Picasa %d, multiples %d' % (
            total_photos, picasa_only, multiple))

    def download_album_media(self):
        print('\nDownloading Picasa Only Files ...')
        # noinspection PyTypeChecker
        for media in DatabaseMedia.get_media_by_search(
                self._root_folder, self._db, media_type=MediaType.PICASA,
                start_date=self.startDate, end_date=self.endDate):
            if os.path.exists(media.local_full_path):
                continue

            # todo add progress bar instead of this print
            if not self.quiet:
                print("  Downloading %s ..." % media.local_full_path)
            tmp_path = os.path.join(media.local_folder, '.gphoto.tmp')

            if not os.path.isdir(media.local_folder):
                os.makedirs(media.local_folder)

            res = Utils.retry(5, urllib.urlretrieve, media.url, tmp_path)
            if res:
                os.rename(tmp_path, media.local_full_path)
            else:
                print("  failed to download %s" % media.local_path)

    def create_album_content_links(self):
        print("\nCreating album folder links to media ...")
        # the simplest way to handle moves or deletes is to clear out all links
        # first, these are quickly recreated anyway
        links_root = os.path.join(self._root_folder, 'albums')
        if os.path.exists(links_root):
            backup_count = len(glob.glob(links_root + '-????'))
            links_backup = '{:s}-{:04d}'.format(links_root, backup_count)
            os.rename(links_root, links_backup)
        for (path, file_name, album_name, end_date) in \
                self._db.get_album_files():
            full_file_name = os.path.join(path, file_name)

            prefix = Utils.string_to_date(end_date).strftime('%Y/%m%d')
            rel_path = u"{0} {1}".format(prefix, album_name)
            link_folder = os.path.join(links_root, rel_path)

            link_file = os.path.join(link_folder, file_name)
            if not os.path.islink(link_file):
                if not os.path.isdir(link_folder):
                    os.makedirs(link_folder)
                os.symlink(full_file_name, link_file)

        print("album links done.\n")
