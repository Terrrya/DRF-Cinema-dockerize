import os
import tempfile

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from cinema.models import Movie, MovieSession, CinemaHall, Genre, Actor
from cinema.serializers import MovieListSerializer, MovieDetailSerializer


MOVIE_SESSION_URL = reverse("cinema:moviesession-list")
MOVIE_URL = reverse("cinema:movie-list")


def image_upload_url(movie_id):
    """Return URL for recipe image upload"""
    return reverse("cinema:movie-upload-image", args=[movie_id])


def detail_movie_url(movie_id):
    return reverse("cinema:movie-detail", kwargs={"pk": movie_id})


def sample_movie(**params) -> Movie:
    defaults = {
        "title": "Test Movie",
        "description": "About test movie",
        "duration": 90,
    }
    defaults.update(params)
    return Movie.objects.create(**defaults)


def sample_movie_session(**params):
    cinema_hall = CinemaHall.objects.create(
        name="Blue", rows=20, seats_in_row=20
    )

    defaults = {
        "show_time": "2022-06-02 14:00:00",
        "movie": None,
        "cinema_hall": cinema_hall,
    }
    defaults.update(params)

    return MovieSession.objects.create(**defaults)


class UnauthenticatedMovieApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self) -> None:
        response = self.client.get(MOVIE_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedMovieApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com", "testpass"
        )
        self.client.force_authenticate(self.user)

    def test_list_movies(self) -> None:
        sample_movie()
        movie_with_genres_actors = sample_movie()

        genre1 = Genre.objects.create(name="genre 1")
        genre2 = Genre.objects.create(name="genre 2")

        movie_with_genres_actors.genres.add(genre1, genre2)

        actor1 = Actor.objects.create(first_name="first1", last_name="last1")
        actor2 = Actor.objects.create(first_name="first2", last_name="last2")

        movie_with_genres_actors.actors.add(actor1, actor2)

        response = self.client.get(MOVIE_URL)
        movies = Movie.objects.all()
        serializer = MovieListSerializer(movies, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_filter_movies_by_title(self) -> None:
        movie1 = sample_movie(title="title1")
        movie2 = sample_movie(title="title2")

        serializer1 = MovieListSerializer(movie1)
        serializer2 = MovieListSerializer(movie2)

        response = self.client.get(MOVIE_URL, {"title": "title1"})

        self.assertIn(serializer1.data, response.data)
        self.assertNotIn(serializer2.data, response.data)

    def test_filter_movies_by_genres(self) -> None:
        movie1 = sample_movie(title="title1")
        movie2 = sample_movie(title="title2")

        genre1 = Genre.objects.create(name="genre 1")
        genre2 = Genre.objects.create(name="genre 2")

        movie1.genres.add(genre1)
        movie2.genres.add(genre2)
        movie3 = sample_movie(title="without genre and actors")

        serializer1 = MovieListSerializer(movie1)
        serializer2 = MovieListSerializer(movie2)
        serializer3 = MovieListSerializer(movie3)

        response = self.client.get(
            MOVIE_URL, {"genres": f"{genre1.id},{genre2.id}"}
        )

        self.assertIn(serializer1.data, response.data)
        self.assertIn(serializer2.data, response.data)
        self.assertNotIn(serializer3.data, response.data)

    def test_filter_movies_by_actors(self) -> None:
        movie1 = sample_movie(title="title1")
        movie2 = sample_movie(title="title2")

        actor1 = Actor.objects.create(first_name="first1", last_name="last1")
        actor2 = Actor.objects.create(first_name="first2", last_name="last2")

        movie1.actors.add(actor1)
        movie2.actors.add(actor2)
        movie3 = sample_movie(title="without genre and actors")

        serializer1 = MovieListSerializer(movie1)
        serializer2 = MovieListSerializer(movie2)
        serializer3 = MovieListSerializer(movie3)

        response = self.client.get(
            MOVIE_URL, {"actors": f"{actor1.id},{actor2.id}"}
        )

        self.assertIn(serializer1.data, response.data)
        self.assertIn(serializer2.data, response.data)
        self.assertNotIn(serializer3.data, response.data)

    def test_retrieve_movie(self) -> None:
        movie = sample_movie()

        movie.genres.add(Genre.objects.create(name="genre"))
        movie.actors.add(
            Actor.objects.create(first_name="first", last_name="last")
        )

        serializer = MovieDetailSerializer(movie)
        url = detail_movie_url(movie.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_movie(self) -> None:
        payload = {
            "title": "test title",
            "description": "test description",
            "duration": 85,
        }

        response = self.client.post(MOVIE_URL, data=payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminMovieApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@test.com",
            "testpass",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_movie(self) -> None:
        payload = {
            "title": "test title",
            "description": "test description",
            "duration": 85,
        }

        response = self.client.post(MOVIE_URL, data=payload)
        movie = Movie.objects.get(id=response.data["id"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for key in payload:
            self.assertEqual(payload[key], getattr(movie, key))

    def test_create_movie_with_genres_and_actors(self) -> None:
        genre1 = Genre.objects.create(name="genre 1")
        genre2 = Genre.objects.create(name="genre 2")

        actor1 = Actor.objects.create(first_name="first1", last_name="last1")
        actor2 = Actor.objects.create(first_name="first2", last_name="last2")

        payload = {
            "title": "test title",
            "description": "test description",
            "duration": 85,
            "genres": [genre1.id, genre2.id],
            "actors": [actor1.id, actor2.id],
        }

        response = self.client.post(MOVIE_URL, data=payload)
        movie = Movie.objects.get(id=response.data["id"])
        genres = movie.genres.all()
        actors = movie.actors.all()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(genres.count(), 2)
        self.assertIn(genre1, genres)
        self.assertIn(genre2, genres)
        self.assertEqual(actors.count(), 2)
        self.assertIn(actor1, actors)
        self.assertIn(actor2, actors)

    def test_delete_movie_not_allowed(self) -> None:
        movie = sample_movie()

        url = detail_movie_url(movie.id)

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_update_movie_not_allowed(self) -> None:
        movie = sample_movie()

        url = detail_movie_url(movie.id)
        payload = {
            "title": "test title",
            "description": "test description",
            "duration": 85,
        }

        response = self.client.put(url, data=payload)

        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_partial_update_movie_not_allowed(self) -> None:
        movie = sample_movie()

        url = detail_movie_url(movie.id)
        payload = {
            "title": "test title",
        }

        response = self.client.patch(url, data=payload)

        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )


class MovieImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@myproject.com", "password"
        )
        self.client.force_authenticate(self.user)
        self.movie = sample_movie()
        self.movie_session = sample_movie_session(movie=self.movie)

    def tearDown(self):
        self.movie.image.delete()

    def test_upload_image_to_movie(self):
        """Test uploading an image to movie"""
        url = image_upload_url(self.movie.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            response = self.client.post(
                url, {"image": ntf}, format="multipart"
            )
        self.movie.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("image", response.data)
        self.assertTrue(os.path.exists(self.movie.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.movie.id)
        response = self.client.post(
            url, {"image": "not image"}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_image_to_movie_list_should_not_work(self):
        url = MOVIE_URL
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            response = self.client.post(
                url,
                {
                    "title": "Title",
                    "description": "Description",
                    "duration": 90,
                    "image": ntf,
                },
                format="multipart",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        movie = Movie.objects.get(title="Title")
        self.assertFalse(movie.image)

    def test_image_url_is_shown_on_movie_detail(self):
        url = image_upload_url(self.movie.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        response = self.client.get(detail_movie_url(self.movie.id))

        self.assertIn("image", response.data)

    def test_image_url_is_shown_on_movie_list(self):
        url = image_upload_url(self.movie.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        response = self.client.get(MOVIE_URL)

        self.assertIn("image", response.data[0].keys())

    def test_image_url_is_shown_on_movie_session_detail(self):
        url = image_upload_url(self.movie.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        response = self.client.get(MOVIE_SESSION_URL)

        self.assertIn("movie_image", response.data[0].keys())

    def test_put_movie_not_allowed(self):
        payload = {
            "title": "New movie",
            "description": "New description",
            "duration": 98,
        }

        movie = sample_movie()
        url = detail_movie_url(movie.id)

        response = self.client.put(url, payload)

        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_delete_movie_not_allowed(self):
        movie = sample_movie()
        url = detail_movie_url(movie.id)

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )
