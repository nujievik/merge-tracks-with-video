import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
from datetime import timedelta

from merge_tracks_with_video.constants import ACCURACY_TIMEDELTA

class _ParseChapters():
    def _extract_base_chapters(self):
        fpath = os.path.join(self.temp_dir, 'chapters.xml')
        if os.path.exists(fpath):
            os.remove(fpath)
        command = ['mkvextract', self.base_video, 'chapters', fpath]
        msg = 'Trying to extract chapters from base video.'
        self.execute(command, msg=msg, get_stdout=False)
        return fpath

    def parse_base_chapters(self):
        fpath = self._extract_base_chapters()
        try:
            tree = ET.parse(fpath)
            root = tree.getroot()
        except Exception:
            return

        to_timedelta = self.timestamp_to_timedelta

        for atom in root.findall('.//ChapterAtom'):
            uid = atom.find('ChapterSegmentUID')
            uid = uid.text.lower() if uid is not None else ''
            self.uids.append(uid)

            start = atom.find('ChapterTimeStart')
            if start is not None:
                start = to_timedelta(start.text)
            self.chap_starts.append(start)

            end = atom.find('ChapterTimeEnd')
            if end is not None:
                end = to_timedelta(end.text)
            self.chap_ends.append(end)

            name = atom.find('.//ChapterDisplay/ChapterString')
            name = name.text if name is not None else ''
            self.names.append(name)

    def correct_none_times(self):
        if all(td is not None for td in self.chap_starts + self.chap_ends):
            return

        lengths = {}
        for idx, uid in enumerate(self.uids):
            if self.starts[idx] is not None:
                start = self.starts[idx]
            else:
                start = lengths.get(uid, timedelta(0))

            end = self.ends[idx]
            if not end:
                for _idx, td in enumerate(self.starts[idx+1:], start=idx+1):
                    if td and uid == self.uids[_idx]:
                        end = td
                        break

            if not end:
                self.set_video_source(uid, exit_on_none=True)
                end = self.merge.files.info.duration(self.source, uid)

            self.chap_starts[idx] = start
            self.chap_ends[idx] = end
            lengths[uid] = lengths.get(uid, timedelta(0)) + end

class Chapters(_ParseChapters):
    def generate_new_chapters(self):
        if not self.chapters:
            return

        root = ET.Element('Chapters')
        edition = ET.SubElement(root, 'EditionEntry')

        ET.SubElement(edition, 'EditionFlagOrdered').text = '1'
        ET.SubElement(edition, 'EditionFlagDefault').text = '1'
        ET.SubElement(edition, 'EditionFlagHidden').text = '0'

        def to_timestamp(td):
            return self.timedelta_to_timestamp(
                td, decimals_place=ACCURACY_TIMEDELTA)

        length = timedelta(0)
        for idx in self.indexes:
            start = length
            end = self.lengths[idx] + length
            name = self.names[idx]

            chapter = ET.SubElement(edition, 'ChapterAtom')

            ET.SubElement(chapter, 'ChapterTimeStart').text = to_timestamp(
                start)
            ET.SubElement(chapter, 'ChapterTimeEnd').text = to_timestamp(end)

            if name:
                chapter_display = ET.SubElement(chapter, 'ChapterDisplay')
                ET.SubElement(chapter_display, 'ChapterString').text = name

            length += end - start

        xml_str = ET.tostring(root, encoding='utf-8', method='xml')
        parsed_xml = minidom.parseString(xml_str)
        pretty_xml_str = parsed_xml.toprettyxml(indent='  ')

        new_chapters = os.path.join(self.temp_dir, 'new_chapters.xml')
        with open(new_chapters, 'w', encoding='utf-8') as f:
            f.write(pretty_xml_str)

        self.merge.chapters = new_chapters
        self.set_opt('chapters', False, self.base_video)
