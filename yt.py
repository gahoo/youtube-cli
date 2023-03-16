from googleapiclient.discovery import build
import json
import os
import argparse
import yaml
import sys
import pdb

config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
with open(config_file, "r") as f:
    config = yaml.safe_load(f)

api_key = config.get('API_KEY')
youtube = build('youtube', 'v3', developerKey=api_key)

def exec(args, command, pageToken=None, depth=1, **kwargs):
    kwargs = {k:v for k,v in kwargs.items() if v is not None}
    sys.stderr.write("Going through page {}\r".format(depth))
    request = getattr(youtube, command)().list(part=args.part, pageToken=pageToken, maxResults=args.maxResults, **kwargs)
    response = request.execute()
    result = extract(response, keys=args.keys)
    if 'nextPageToken' in response and response['pageInfo']['resultsPerPage'] * depth < args.maxResults:
        result = result + exec(args, command, response['nextPageToken'], depth + 1, **kwargs)
    return result

def extract(response, keys):
    result=[]
    for item in response['items']:
        parts={}
        for part in args.part.split(','):
            if isinstance(item[part], dict):
                parts.update({k:v for k,v in item[part].items() if k in keys})
            elif isinstance(item[part], list):
                pass
            else:
                parts.update({part: item[part]})
        result.append(parts)
    return result

channels = lambda args:exec(args, command='channels', id=args.channel_id)
videos = lambda args:exec(args, command='videos', id=args.video_id)
playlists = lambda args:exec(args, command='playlists', channelId=args.channel_id, id=args.playlist_id)
playlistitems = lambda args:exec(args, command='playlistItems', playlistId=args.playlist_id)
search = lambda args:exec(args, command='search', q=args.query, type=args.type, channelId=args.channel_id)

parser = argparse.ArgumentParser(description="YouTube command line tool")

subparsers = parser.add_subparsers(help='sub-command help')

search_parser = subparsers.add_parser('search', aliases=['q'], help='search help')
search_parser.add_argument('--query', type=str, help='the query to search for')
search_parser.add_argument('--channel_id', type=str, help='the ID of the channel to fetch playlist for')
search_parser.add_argument('--part', type=str, help='what to fetch(id,snippet,contentDetails,status,...)', default='id,snippet')
search_parser.add_argument('--keys', type=str, nargs="*",default=['kind', 'videoId', 'channelId', 'publishedAt', 'title', 'description', ], help='what field to show')
search_parser.add_argument('--type', type=str, default='channel', help='what kind to search(channel,playlist,video)')
search_parser.add_argument('--maxResults', type=int, help='How many results per page', default=5)
search_parser.set_defaults(func=search)

playlists_parser = subparsers.add_parser('playlists', aliases=['pl'], help='playlist help')
playlists_parser.add_argument('--playlist_id', type=str, help='the ID of the playlist to fetch')
playlists_parser.add_argument('--channel_id', type=str, help='the ID of the channel to fetch playlist for')
playlists_parser.add_argument('--part', type=str, help='what to fetch(id,snippet,contentDetails,status,...)', default='id,contentDetails,snippet')
playlists_parser.add_argument('--keys', type=str, nargs="*",default=['channelId', 'channelTitle', 'title', 'description', 'publishedAt', 'itemCount', 'embedHtml'], help='what field to show')
playlists_parser.add_argument('--maxResults', type=int, help='How many results per page', default=50)
playlists_parser.set_defaults(func=playlists)

playlistItems_parser = subparsers.add_parser('playlistitems', aliases=['pli'],  help='playlist help')
playlistItems_parser.add_argument('--playlist_id', type=str, help='the ID of the channel to fetch playlist for')
playlistItems_parser.add_argument('--part', type=str, help='what to fetch(id,snippet,contentDetails,status,...)', default='contentDetails,snippet')
playlistItems_parser.add_argument('--keys', type=str, nargs="*",default=['videoId', 'videoPublishedAt', 'playlistId', 'channelId', 'title'], help='what field to show')
playlistItems_parser.add_argument('--maxResults', type=int, help='How many results per page', default=50)
playlistItems_parser.set_defaults(func=playlistitems)


channels_parser = subparsers.add_parser('channels', aliases=['c'], help='channels help')
channels_parser.add_argument('--channel_id', type=str, help='the ID of the channels to fetch')
channels_parser.add_argument('--part', type=str, help='what to fetch(id,snippet,contentDetails,status,...)', default='id,snippet')
channels_parser.add_argument('--keys', type=str, nargs="*",default=['title', 'description', 'customUrl', 'publishedAt'], help='what field to show')
channels_parser.add_argument('--maxResults', type=int, help='How many results per page', default=50)
channels_parser.set_defaults(func=channels)

videos_parser = subparsers.add_parser('videos', aliases=['v'], help='videos help')
videos_parser.add_argument('--video_id', type=str, help='the ID of the videos to fetch')
videos_parser.add_argument('--part', type=str, help='what to fetch(id,snippet,contentDetails,status,...)', default='id,snippet')
videos_parser.add_argument('--keys', type=str, nargs="*",default=['id','publishedAt', 'channelId', 'channelTitle', 'title'], help='what field to show')
videos_parser.add_argument('--maxResults', type=int, help='How many results per page', default=50)
videos_parser.set_defaults(func=videos)

def add_share_argument(x):
    x.add_argument('--output', type=str, choices=['json', 'tsv'], default='tsv', help='the format of the output')

list(map(add_share_argument, [search_parser, playlists_parser, playlistItems_parser, channels_parser, videos_parser]))


if __name__ == "__main__":
    args = parser.parse_args()
    if hasattr(args, 'func') and callable(args.func):
        result = args.func(args)
        if args.output == 'json':
            print(json.dumps(result))
        elif args.output == 'tsv':
            print("\n".join(["\t".join([str(e) for e in r.values()]) for r in result]))
    else:
        parser.print_help()
