from datetime import date

"""This file describes the contents of the test account photos library"""


class TestAccount:
    latest_date = date(2020, 4, 26)

    image_years = [2020, 2019, 2017, 2016, 2015, 2014, 2001, 2000, 1998, 1965]
    # 10 images in each of the years in the test data
    # plus 5 shared items in the 2017 shared album
    images_per_year = [1, 0, 10, 10, 10, 10, 10, 10, 10, 10]
    shared_images_per_year = [0, 0, 5, 0, 0, 0, 0, 0, 0, 0]
    shared_album_images_per_year = [0, 6, 0, 0, 0, 0, 0, 0, 0, 0]
    videos_per_year = [0, 0, 10, 0, 0, 0, 0, 0, 0, 0, 0]

    image_count = sum(images_per_year)
    shared_image_count = sum(shared_images_per_year)
    video_count = sum(videos_per_year)
    total_count = image_count + video_count

    # shared test album has 'show in albums' so does appear in our albums list
    # 5 of its files are ours and 5 shared by the real giles knap
    album_names = [
        r"1001?Shared?Test?Album",
        r"0101?Album?2001",
        r"0528?Movies",
        r"0923?Clones😀",
        r"0926?Album?2016",
        r"1207?Same?Names",
        r"0426?Name?with?Comma",
    ]
    album_years = [2019, 2001, 2017, 2017, 2016, 2014, 2020]
    album_images = [5, 10, 10, 4, 16, 10, 1]
    album_shared_images = [5, 0, 0, 0, 0, 0, 0]
    album_count = len(album_names)
    album_image_count = sum(album_images)
    album_shared_image_count = sum(album_shared_images)

    shared_album_names = [r"0220?Noah?s?transformer?lego"]
    shared_album_images = [0]
    shared_album_shared_images = [6]
    shared_album_count = len(shared_album_names)
    shared_album_image_count = sum(shared_album_images)
    shared_album_shared_image_count = sum(shared_album_shared_images)

    # subset of items from 2016-01-01 to 2017-01-01 for quicker tests
    start = "2016-01-01"
    end = "2017-01-01"
    image_count_2016 = 10
    item_count_2017 = 20
    item_count_2020 = 1
