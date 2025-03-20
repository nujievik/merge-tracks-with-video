from datetime import timedelta

ACCEPT_OFFSETS = {
    'video': timedelta(milliseconds=5000),
    'audio': timedelta(milliseconds=100)
}

audio_list = []
base_dir_fpaths = []
retimed_audio = []
retimed_subtitles = []
subtitles_list = []

chap_starts = []
chap_ends = []
starts = []
ends = []

indexes = []
names = []
segments_vid = []
segments_times = []
uids = []

lengts = {}
offsets_start = {}
offsets_end = {}
segments = {}
segments_inds = {}
sources = {}
uid_info = {}

skips = set()

base_dir = ''
base_video = ''
defacto_start = ''
defacto_end = ''
duration = ''
end = ''
file_type = ''
length = ''
offset_start = ''
offset_end = ''
retimed = ''
segment = ''
source = ''
start = ''
strict = ''
temp_dir = ''
uid = ''

audio_cnt = 0
ind = 0
ind_end = 0
tid = 0

chapters = True
extracted_orig = False
is_splitted = False
orig_audio = True
orig_subtitles = True
