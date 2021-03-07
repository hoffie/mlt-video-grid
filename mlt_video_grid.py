#!/usr/bin/env python3
import math
import os
import argparse
import xml.etree.ElementTree as ET


def make_property(name, value):
    r = ET.Element('property', {'name': name})
    r.text = value
    return r

def make_filter(name, producer_id, properties):
    id = 'filter%s%s%s%s' % (
        name[0].upper(),
        name[1:],
        producer_id[0].upper(),
        producer_id[1:],
    )
    f = ET.Element('filter', id=id)
    f.append(make_property('mlt_service', name))
    for name, value in properties.items():
        f.append(make_property(name, value))
    return f

def make_qtcrop_filter(producer_id, left, top, width, height):
    properties = {
        'rect': '%d %d %d %d 1' % (left, top, width, height),
        'circle': '0',
        'color': '#00000000',
        'radius': '0',
        'shotcut:filter': 'cropRectangle',
    }
    return make_filter('qtcrop', producer_id, properties)

def make_affine_filter(producer_id, left, top, width, height, zoom):
    properties = {
        'background': 'color:#00000000',
        'shotcut:filter': 'affineSizePosition',
        'transition:fill': '1',
        'transition:distort': '0',
        'transition.rect': '%d %d %d %d 1' % (left - (width*zoom - width)/2, top - (height*zoom - height)/2, width*zoom, height*zoom),
        'transition.valign': 'middle',
        'transition.halign': 'center',
        'shotcut:animIn': '00:00:00.000',
        'shotcut:animOut': '00:00:00.000',
        'transition.threads': '0',
        'transition.fix_rotate_x': '0',
    }
    return make_filter('affine', producer_id, properties)


def make_audio_transition(producer_id, a_track, b_track):
    # This is required so that audio from all tracks can be heard
    id = 'MixAudio%s%sToBase' % (producer_id[0].upper(), producer_id[1:])
    properties = {
        'a_track': '%d' % a_track,
        'b_track': '%d' % b_track,
        'mlt_service': 'mix',
        'always_active': '1',
        'sum': '1',
    }
    return make_transition(id, properties)


def make_video_transition(producer_id, a_track, b_track):
    # This is required in order to be able to see all videos at once
    id = 'MixVideo%s%sToBase' % (producer_id[0].upper(), producer_id[1:])
    properties = {
        'a_track': '%d' % a_track,
        'b_track': '%d' % b_track,
        'version': '0.9',
        'mlt_service': 'frei0r.cairoblend',
        'disable': '0',
        '1': 'normal',
    }
    return make_transition(id, properties)


def make_transition(id, properties):
    t = ET.Element('transition', id='transition%s' % id)
    for name, value in properties.items():
        t.append(make_property(name, value))
    return t


class VideoGrid(object):
    _producer_id = -1
    _playlist_id = -1
    main_audio_track_nr = 0
    main_video_track_nr = 1
    videos_added = 0
    fill = 0

    def __init__(self, input_mlt, column_count, video_count, blank):
        self.column_count = column_count
        self.row_count = math.ceil(video_count / column_count)
        self.video_count = video_count
        self.blank = blank
        self.xml = ET.parse(input_mlt)
        self.total_width = self._get_total_width()
        self.total_height = self._get_total_height()
        self.single_video_width = self.total_width // self.column_count
        self.single_video_height = self.total_height // self.row_count
        for x, el in enumerate(self.xml.getroot()):
            if el.tag == 'tractor':
                self._next_insert_position = x
                break

    def _get_total_width(self):
        return int(self.xml.find('profile').attrib.get('width'))

    def _get_total_height(self):
        return int(self.xml.find('profile').attrib.get('height'))

    def add_video(self, resource):
        self.videos_added += 1
        if resource == 'FILL':
            self.fill += 1
            return
        basename = os.path.basename(resource)
        producer_id = 'producerVideoGrid%d' % self.next_producer_id()
        pr = ET.Element('producer', {'id': producer_id})
        properties = {
            'resource': resource,
            'eof': 'pause',
            'audio_index': '1',
            'video_index': '0',
            'mute_on_pause': '0',
            'mlt_serviec': 'avformat-novalidate',
            'seekable': '1',
            'aspect_ratio': '1',
            'ignore_points': '0',
            'shotcut:caption': basename,
            'global_feed': '1',
            'xml': 'was here',
        }
        for name, value in properties.items():
            pr.append(make_property(name, value))
        col = (self.videos_added-1-self.fill) % self.column_count
        row = (self.videos_added-1) // self.column_count
        left = col * self.single_video_width
        top = row * self.single_video_height
        width = self.single_video_width * (1 + self.fill)
        height = self.single_video_height
        self.fill = 0
        pr.append(make_affine_filter(producer_id, left, top, width, height, 1.4))
        pr.append(make_qtcrop_filter(producer_id, left, top, width, height))
        pos = self.next_insert_position()
        self.xml.getroot().insert(pos, pr)

        playlist_id = 'playlistVideoGrid%d' % self.next_playlist_id()
        pl = ET.Element('playlist', {'id': playlist_id})
        pl.append(make_property('shotcut:video', '1'))
        pl.append(make_property('shotcut:name', basename))
        pl.append(ET.Element('blank', {'length': self.blank}))
        pl.append(ET.Element('entry', {'producer': producer_id, 'in': '00:00:00.000'}))
        self.xml.getroot().insert(pos+1, pl)

        tractor = self.xml.find('tractor')
        tractor.append(ET.Element('track', {'producer': playlist_id, 'hide': 'audio'}))
        track_nr = self.get_track_number_by_producer(playlist_id)
        tractor.append(make_video_transition(playlist_id, self.main_video_track_nr, track_nr))
        # This should be unneeded but avoids unexpected behavior (i.e. when
        # trying to listen to the track's audio temporarily):
        tractor.append(make_audio_transition(playlist_id, self.main_audio_track_nr, track_nr))

    def next_producer_id(self):
        self._producer_id += 1
        return self._producer_id

    def next_playlist_id(self):
        self._playlist_id += 1
        return self._playlist_id

    def next_insert_position(self):
        self._next_insert_position += 1
        return self._next_insert_position - 1

    def get_track_number_by_producer(self, producer_id):
        n = 0
        for track in self.xml.getroot().find('tractor').findall('track'):
            if track.attrib['producer'] == producer_id:
                return n
            n += 1
        raise RuntimeError('track not found')

    def write(self, output_mlt):
        self.xml.write(output_mlt)


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('-i', '--input-mlt', type=str, required=True)
    cli.add_argument('-o', '--output-mlt', type=str, required=True)
    cli.add_argument('-c', '--columns', type=int, required=True)
    cli.add_argument('-b', '--blank', type=str, default='00:0:00.000')
    cli.add_argument('videos', nargs='+')
    args = cli.parse_args()
    vg = VideoGrid(
        input_mlt=args.input_mlt,
        column_count=args.columns,
        video_count=len(args.videos),
        blank=args.blank,
    )
    for video in args.videos:
        vg.add_video(video)
    vg.write(args.output_mlt)


if __name__ == '__main__':
    main()
