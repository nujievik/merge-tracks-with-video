from datetime import timedelta

ACCEPT_OFFSETS = {
    'video': timedelta(milliseconds=5000),
    'audio': timedelta(milliseconds=100)
}

audio_list = []
subs_list = []
retimed_audio = []
retimed_subs = []

uids = []
chap_starts = []
chap_ends = []
names = []
indexes = []
segments_vid = []
segments_times = []
starts = []
ends = []

segments = {}
segments_inds = {}
uid_info = {}
sources = {}
lengts = {}
offsets_start = {}
offsets_end = {}

skips = set()

temp_dir = ''
video = ''
source = ''
segment = ''
retimed = ''
uid = ''
duration = ''
file_type = ''
strict = ''
start = ''
end = ''
defacto_start = ''
defacto_end = ''
offset_start = ''
offset_end = ''
length = ''

tid = 0
ind = 0
ind_end = 0
audio_cnt = 0
subs_cnt = 0

splitted = False
extracted_orig = False
orig_audio = True
orig_subs = True
chapters = True
