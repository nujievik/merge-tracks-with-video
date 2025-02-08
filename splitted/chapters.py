import os
from xml.dom import minidom
from datetime import timedelta
import xml.etree.ElementTree as ET

import type_convert
import merge.params
import options.manager
import file_info.by_ffprobe
from . import params, video

def set_chapters_info(file_chapters):
    params.uids = []
    params.chap_starts, params.chap_ends = [], []
    params.names = []

    try:
        tree = ET.parse(file_chapters)
        root = tree.getroot()
    except Exception:
        return

    for atom in root.findall('.//ChapterAtom'):
        uid = atom.find('ChapterSegmentUID')
        uid = uid.text.lower() if uid is not None else ''
        params.uids.append(uid)

        start = atom.find('ChapterTimeStart')
        if start is not None:
            start = type_convert.str_to_timedelta(start.text)
        params.chap_starts.append(start)

        end = atom.find('ChapterTimeEnd')
        if end is not None:
            end = type_convert.str_to_timedelta(end.text)
        params.chap_ends.append(end)

        name = atom.find('.//ChapterDisplay/ChapterString')
        name = name.text if name is not None else ''
        params.names.append(name)

def correct_chapters_times():
    if any(td is None for td in params.chap_starts + params.chap_ends):
        lengths = {}

        for ind, params.uid in enumerate(params.uids):
            if params.chap_starts[ind] is not None:
                start = params.chap_starts[ind]
            else:
                start = lengths.get(params.uid, timedelta(0))

            end = params.chap_ends[ind]

            if not end:
                for temp_ind, time in enumerate(params.chap_starts[ind+1:],
                                                start=ind+1):
                    if time and params.uid == params.uids[temp_ind]:
                        end = time
                        break

            if not end:
                video.set_video_source(exit_if_none=True)
                end = file_info.by_ffprobe.get_duration_split_source()

            params.chap_starts[ind] = start
            params.chap_ends[ind] = end
            lengths[params.uid] = lengths.get(params.uid, timedelta(0)) + end

    for ind, params.uid in enumerate(params.uids):
        if (video.set_video_source() and
            params.chap_ends[ind] > (
                file_info.by_ffprobe.get_duration_split_source())
            ):
            # Real playback time does not exceed the duration of the video
            # or audio track
            end = file_info.by_ffprobe.get_duration_split_source()
            params.chap_ends[ind] = end

def generate_new_chapters():
    if not params.chapters:
        return

    root = ET.Element('Chapters')
    edition = ET.SubElement(root, 'EditionEntry')

    ET.SubElement(edition, 'EditionFlagOrdered').text = '1'
    ET.SubElement(edition, 'EditionFlagDefault').text = '1'
    ET.SubElement(edition, 'EditionFlagHidden').text = '0'

    length = timedelta(0)
    for ind in params.indexes:
        start = length
        end = params.lengths[ind] + length
        name = params.names[ind]

        chapter = ET.SubElement(edition, 'ChapterAtom')

        ET.SubElement(chapter, 'ChapterTimeStart').text = (
            type_convert.timedelta_to_str(
                start, hours_place=2, decimal_place=6))
        ET.SubElement(chapter, 'ChapterTimeEnd').text = (
            type_convert.timedelta_to_str(end, 2, 6))

        if name:
            chapter_display = ET.SubElement(chapter, 'ChapterDisplay')
            ET.SubElement(chapter_display, 'ChapterString').text = name

        length += end - start

    xml_str = ET.tostring(root, encoding='utf-8', method='xml')
    parsed_xml = minidom.parseString(xml_str)
    pretty_xml_str = parsed_xml.toprettyxml(indent='  ')

    new_chapters = os.path.join(params.temp_dir, 'new_chapters.xml')
    with open(new_chapters, 'w', encoding='utf-8') as f:
        f.write(pretty_xml_str)

    merge.params.new_chapters = new_chapters
    options.manager.set_target_option(params.base_video, 'chapters', False)
