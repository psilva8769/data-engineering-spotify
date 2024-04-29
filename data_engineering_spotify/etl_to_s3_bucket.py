import json
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import boto3
import json
from datetime import datetime
from io import StringIO
import pandas as pd

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    bucket = 'data-engineering-project-eckesaht'
    key_prefix = 'raw_data/to_processed/'

    # EXTRACT
    sp = setup_spotify_client()
    playlist_uri = 'spotify:playlist:37i9dQZEVXbMDoHDwVN2tF'  # Directly using the Spotify URI format
    spotify_data = fetch_playlist_data(sp, playlist_uri)

    # TRANSFORM
    # Assuming `data` is the fetched Spotify data
    album_data = transform_album_data(data['items'])
    artist_data = transform_artist_data(data['items'])
    song_data = transform_song_data(data['items'])

    # Generating keys for each data type
    album_key = f'{key_prefix}albums_{datetime.now()}.json'
    artist_key = f'{key_prefix}artists_{datetime.now()}.json'
    song_key = f'{key_prefix}songs_{datetime.now()}.json'

    # LOAD
    # Uploading transformed data to S3
    load_to_s3(s3, bucket, album_key, album_data)
    load_to_s3(s3, bucket, artist_key, artist_data)
    load_to_s3(s3, bucket, song_key, song_data)

# EXTRACT
def setup_spotify_client():
    """
    Sets up the Spotify client using OAuth credentials from environment variables.
    """
    client_id = os.environ.get('SPOTIFY_CLIENT_ID')
    client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET')
    redirect_uri = os.environ.get('SPOTIFY_REDIRECT_URI')
    
    auth_manager = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)
    return spotipy.Spotify(auth_manager=auth_manager)

def fetch_playlist_data(sp_client, playlist_uri):
    """
    Fetches data for a given Spotify playlist URI using the provided Spotify client.
    """
    return sp_client.playlist_tracks(playlist_uri)

# TRANSFORM
def transform_album_data(track_items):
    """
    Transforms album data from Spotify track items.
    """
    return [
        {
            'album_id': item['track']['album']['id'],
            'name': item['track']['album']['name'],
            'release_date': item['track']['album']['release_date'],
            'total_tracks': item['track']['album']['total_tracks'],
            'url': item['track']['album']['external_urls']['spotify']
        }
        for item in track_items if 'album' in item['track']
    ]

def transform_artist_data(track_items):
    """
    Transforms artist data from Spotify track items.
    """
    artists = []
    for item in track_items:
        if 'track' in item and 'artists' in item['track']:
            for artist in item['track']['artists']:
                artists.append({
                    'artist_id': artist['id'],
                    'artist_name': artist['name'],
                    'external_url': artist['href']
                })
    return artists

def transform_song_data(track_items):
    """
    Transforms song data from Spotify track items.
    """
    return [
        {
            'song_id': item['track']['id'],
            'song_name': item['track']['name'],
            'duration_ms': item['track']['duration_ms'],
            'url': item['track']['external_urls']['spotify'],
            'popularity': item['track']['popularity'],
            'song_added': item['added_at'],
            'album_id': item['track']['album']['id'],
            'artist_id': item['track']['album']['artists'][0]['id']
        }
        for item in track_items if 'track' in item
    ]

# LOAD
def load_to_s3(s3_client, bucket, key, data):
    """
    Uploads data to the specified S3 bucket with the given key.
    """
    s3_client.put_object(Bucket=bucket, Key=key, Body=json.dumps(data))
