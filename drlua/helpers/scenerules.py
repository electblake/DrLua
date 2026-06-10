from __future__ import annotations

from collections.abc import Iterable, Mapping
import enum
from pathlib import Path
import re
from datetime import datetime
from functools import total_ordering

from drlua.config import SCENE_NAME_SEP, DateFormatTyperOption

class ReleaseName:
    _name_tags: set[NameTag]

    def __init__(self, **kwargs):
        self._name_tags = set()
        if name_tags := kwargs.get("name_tags"):
            self._add_name_tags(name_tags)
        if name := kwargs.get("name"):
            self.addRoleValue(NameTag.Role.Name, name)
        if date_format := kwargs.get("date_format"):
            if date_format == DateFormatTyperOption.long:
                self.addRoleValue(NameTag.Role.LongDate, True)
            elif date_format == DateFormatTyperOption.short:
                self.addRoleValue(NameTag.Role.ShortDate, True)
        if tag := kwargs.get("tag"):
            for item in tag:
                self.addRoleValue(NameTag.Role.Tag, item)
        if section := kwargs.get("section"):
            self.addRoleValue(NameTag.Role.Section, section)
        if group_name := kwargs.get("group_name"):
            self.addRoleValue(NameTag.Role.Group, group_name)

    def _add_name_tags(self, name_tags: object) -> None:
        if isinstance(name_tags, ReleaseName):
            self._name_tags.update(name_tags._name_tags)
            return
        if isinstance(name_tags, NameTag):
            self._name_tags.add(name_tags)
            return
        if isinstance(name_tags, Mapping):
            for role, value in name_tags.items():
                self.addRoleValue(role, value)
            return
        if isinstance(name_tags, Iterable) and not isinstance(name_tags, str):
            for item in name_tags:
                if isinstance(item, NameTag):
                    self._name_tags.add(item)
                    continue
                if isinstance(item, tuple) and len(item) == 2:
                    role, value = item
                    self.addRoleValue(role, value)
                    continue
                raise TypeError(f"Unsupported name_tags item: {item!r}")
            return
        raise TypeError(f"Unsupported name_tags value: {name_tags!r}")

    def addRoleValue(self, role: int, value):
        if value is None:
            return
        tag = NameTag(role, value)
        self._name_tags.add(tag)

    def text(self):
        tags = sorted(self._name_tags)
        group = [t for t in tags if t.role == NameTag.Role.Group]
        normal = [t for t in tags if t.role != NameTag.Role.Group]

        text = SCENE_NAME_SEP.join(t.text() for t in normal)

        if group:
            return f"{text}-{group[0].text()}"

        return text

    def tagWithRole(self, role: int) -> NameTag | None:
        matches = sorted(tag for tag in self._name_tags if tag.role == role)
        return matches[0] if matches else None

    def tagsWithRole(self, role: int) -> list[NameTag]:
        return sorted(tag for tag in self._name_tags if tag.role == role)

    def textWithRole(self, role: int) -> str | None:
        tag = self.tagWithRole(role)
        return tag.text() if tag is not None else None
    def text_name_tags(self):
        return [tag_item.text() for tag_item in self.tagsWithRole(NameTag.Role.Tag)]

    def parent_text(self):
        name = self.tagWithRole(NameTag.Role.Name)
        date = self.tagWithRole(NameTag.Role.LongDate) or self.tagWithRole(NameTag.Role.ShortDate)
        date = date.text() if date else ""
        name = name.text() if name is not None else self.text()
        return f"{name}{SCENE_NAME_SEP}{date}"

    def file_name(self):
        return Path(f"{self.text()}.lua")

@total_ordering
class NameTag:
    role: int

    def __init__(self, role: int, value):
        self.role = role
        self.value = value

    class Role(enum.IntEnum):
        Name = 0x64
        LongDate = 0xc9
        ShortDate = 0xca
        Title = 0x12c
        Tag = 0x190
        Section = 0x1f4
        Group = 0x29a

    def __str__(self) -> str:
        return self.text()

    def text(self):
        if self.role == type(self).Role.LongDate:
            return datetime.now().strftime("%Y.%m.%d")
        if self.role == type(self).Role.ShortDate:
            return datetime.now().strftime("%y.%m.%d")

        text = str(SCENE_NAME_SEP.join([
            token[0:1].upper() + token[1:].lower()
            for token in self._tokens()
            if token
        ]))
        if self.role == type(self).Role.Section:
            text = text.upper()
        return text

    def _tokens(self):
        values = self.value if isinstance(self.value, list) else [self.value]
        tokens = []
        for value in values:
            tokens.extend(re.findall(r"[A-Za-z0-9]+", str(value)))
        return tokens

    def _sort_key(self) -> tuple[int, str]:
        return (self.role, self.text().casefold())

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, NameTag):
            return NotImplemented
        return self._sort_key() < other._sort_key()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NameTag):
            return NotImplemented
        return self._sort_key() == other._sort_key()

    def __hash__(self) -> int:
        return hash(self._sort_key())

# # https://scenerules.org/nfo/2010.1_0DAY.nfo
# # https://scenerules.org/nfo/2020_X265.nfo
# # https://scenerules.org/nfo/2023_NSW.nfo
# # https://scenerules.org/nfo/2008_XXXPAY.nfo


# High Definition x264 and Ultra High Definition x265 Standards
# Revision 5.0 - 2020-04-15

# [ Intro ]
# Since the last revision, which was almost a decade ago, advancements have been made and HD Retail has been left in the dark
# ages.

# x265 and UHD have come into play, CRF has surpassed 2-pass in maintaining consistent quality, becoming the standard encoding
# method in every other video section.

# Simply put, this new revision brings retail into the 21st century, allowing for quality releases by following the standard
# values, while also affording the freedoms necessary for groups to take things a step further and provide excellent quality
# releases.

# No longer are encodes constrained to bitrates or rules meant for cheap playback devices. Welcome to the 21st century and
# welcome back to quality.

# Compliance with this document is optional as of its pre date, and mandatory as of 2020-05-11 00:00:00 UTC (1589155200 Unix
# time).

# 1) [ Retail Sources ]
#     1.1) Retail sources are considered as content distributed by studios via legitimate retail discs.
#         1.1.1) Allowed formats include, but are not limited to: Blu-ray, Ultra HD Blu-ray, HD DVD.
#         1.1.2) Blu-ray discs must be tagged as BluRay.
#         1.1.3) Ultra HD Blu-ray discs must be tagged as UHD.BluRay.
#         1.1.4) HD DVD discs must be tagged as HDDVD.
#         1.1.5) Music discs must be tagged as MBluRay or UHD.MBluRay, must comply with the directory format specified in rule
#                18.4.7, and are:
#             1.1.5.1) Exempt from rules 8.14, 10.2 and 18.5.7.
#             1.1.5.2) Only allowed for musical performances or events, not documentaries with live footage.
#             1.1.5.3) Allowed to use the PURE tag, which must only be used for audio releases (e.g. albums) and must comply
#                      with the directory format specified in rule 18.4.8.
#                 1.1.5.3.1) PURE releases are only allowed to be released at the source resolution.
#                            e.g. Source is 1080p, therefore a 720p release is not allowed.

# 2) [ Non-retail Sources ]
#     2.1) Non-retail sources are considered as content that is not distributed by studios via retail techniques.
#         2.1.1) Non-retail formats include, but are not limited to: cam, bootlegs, workprints, screeners.
#     2.2) Sources with visual or audible watermarks must be mentioned in the NFO.
#          e.g. Black-and-white scenes and timecode counters.
#     2.3) Non-retail sources are only exempt from the following rules:
#         2.3.1) Rule 15 - Proof. No proof is required.
#         2.3.2) Rule 3.7 - Any non-critical feature footage (e.g. credits, opening studio logos) may be removed at the
#                discretion of the group.
#         2.3.3) Rule 12.5 - Measures may be taken to conceal watermarks present in any stream, it is recommended to use the
#                least destructive method possible.
#     2.4) Non-retail elements must use the appropriate tag. e.g. LINE.

# 3) [ Video ]
#     3.1) Transcoding of transcoded or lossy material is not allowed.
#     3.2) Multiple video tracks are not allowed.
#     3.3) Must be free from technical flaws.
#         3.3.1) Technical flaws include, but are not limited to: sync issues, interlacing, lack of IVTC, bad aspect ratio,
#                invalid resolution, unrelated footage, warnings, glitches not present on source, under-crop, over-crop.
#     3.4) Dupes based on source type or disc format are not allowed.
#     3.5) Left-eye or right-eye video streams from a 3D source must not be used for a 2D release.
#         3.5.1) Except for titles that were released exclusively in 3D and that have no upcoming 2D disc planned.
#         3.5.2) Except for cases when 4.7.1 applies and there is no 2D source available or planned to be released.
#     3.6) Single features must not be split across multiple files.
#         3.6.1) Sources where the opening credits and closing credits span multiple discs must be encoded and released as a
#                single release.
#                e.g. Disc 1: Opening credits and first 105 minutes of feature.
#                     Disc 2: Remaining 122 minutes of feature and closing credits.
#                     Release: A single 227 minute feature.
#         3.6.2) Sources with multiple episodes, parts etc., that are in a single video file, must be split into individual
#                releases if there is a clear delineation between them, such as credits.
#                e.g. Disc contains 10 episodes in a single m2ts file with all episodes strung together with credits between
#                     every episode, each episode must be released separately.
#     3.7) Non-feature footage including, but not limited to: credits, previously on, intertitles must not be removed or encoded
#          separately.
#         3.7.1) In situations of a progressive feature containing interlaced non-feature footage, the interlaced footage may be
#                left interlaced, or only that footage must be deinterlaced.
#                e.g. Only the credits are interlaced, you may leave them interlaced or only apply a deinterlacer to the
#                     credits, not the entire video.
#     3.8) Unrelated footage must be removed.
#         3.8.1) Unrelated footage includes, but is not limited to: content warnings, studio worksheets, test screens, piracy
#                warnings.
#     3.9) English-spoken features must not contain foreign overlays for relevant on-screen information.
#         3.9.1) Relevant on-screen information includes, but is not limited to: location titles, hardcoded subtitles,
#                introduction text, or any other information essential to the plot of the feature.
#         3.9.2) Non-relevant on-screen information includes: opening credits, movie title, closing credits.
#         3.9.3) For discs where relevant on-screen information is included in the form of English subtitles instead of
#                overlays, these subtitles must be included as a forced track (see 10.2). If the disc does not include them in
#                English, it is not allowed to omit them and release the feature without them, as it is still considered
#                relevant information.
#     3.10) Using multiple retail video sources of the same movie is allowed and must not be encoded separately. Each source and
#           what content came from which must be noted in the NFO.
#           e.g. Feature from German BluRay with credits from American BluRay to avoid German translated credits, as the German
#                BluRay had better quality for the feature.

# 4) [ Resolution / Aspect Ratio ]
#     4.1) 720p refers to a maximum display resolution of 1280x720.
#         4.1.1) For aspect ratios greater than or equal to 1.78:1, horizontal pixel width must be 1280 pixels.
#                e.g. Source aspect ratio of 2.40:1 will resize to 1280x534.
#         4.1.2) For aspect ratios less than or equal to 1.78:1, vertical pixel height must be 720 pixels.
#                e.g. Source aspect ratio of 1.33:1 will resize to 960x720.
#     4.2) 1080p refers to a maximum display resolution of 1920x1080.
#     4.3) 2160p refers to a maximum display resolution of 3840x2160.
#     4.4) Resolution must be mod2.
#     4.5) Upscaling is not allowed.
#         4.5.1) 1080p from a 1080p source and 2160p from a 2160p source encodes must only be cropped, no resizing is allowed.
#         4.5.2) In situations where cropping is needed vertically and/or horizontally, resolutions are allowed to be under the
#                max height or width. e.g. 1080p at 1916x1072 is acceptable.
#         4.5.3) In situations where the source video stream does not meet the minimum requirements for 1080p/2160p, the video
#                must be resized down to 720p/1080p and a source sample must be included.
#     4.6) 3D must only be done at 1080p or 2160p resolutions.
#     4.7) Dupes based on resolution are not allowed.
#         4.7.1) Releases with an AR difference of at least 5% to the previous release are not considered a dupe. These releases
#                must be tagged as WS, FS or OM (open matte), not PROPER, and the original release must not be nuked. Original
#                aspect ratio (OAR) releases are always allowed.
#             4.7.1.1) AR difference example:
#                      Old release resolution (after crop) is 1920x1040
#                      New release resolution (after crop) is 1440x1080
#                      OldReleaseAR = 1920 / 1040 = 1.846
#                      NewReleaseAR = 1440 / 1080 = 1.333
#                      (OldReleaseAR - NewReleaseAR) / [(OldReleaseAR + NewReleaseAR) / 2] = AR difference
#                      |AR difference * 100| = AR difference (%)
#                      (1.846 - 1.333) / [(1.846 + 1.333) / 2] = 0.322
#                      |0.322 * 100| = 32.2%
#                      32.2% is greater than the 5% minimum, therefore the new release is not considered a dupe.
#     4.8) Black borders, and anything that is not part of the feature, must be cropped.
#         4.8.1) Black borders include, but are not limited to: black or colored borders, duplicate lines, dirty lines or
#                pixels.
#         4.8.2) Retention or removal of faded edges is left to the discretion of the group. Inclusion of faded edges is not
#                considered a technical flaw.
#             4.8.2.1) Faded edges refers to a line of pixels which are of similar appearance to pixels parallel to the video
#                      frame.
#             4.8.2.2) Releases which include faded edges must consider faded edges as a valid part of the video frame and do
#                      not count as black borders.
#                      e.g. A release cannot be propered if 1 pixel of faded edges and 1 pixel of black exists.
#         4.8.3) In the case of varying aspect ratios throughout the feature, video must be cropped to the widest frame.
#             4.8.3.1) Studio logos and credits must be disregarded when determining the widest frame.
#         4.8.4) Situations where video cropping of the same content varies between sources are not considered a technical flaw,
#                and may not be propered.
#     4.9) Video can be over or under-cropped by a maximum of 1 pixel per side. Over or under-cropping by more than 1 pixel per
#          side is considered a technical flaw.
#         4.9.1) Under-crop refers to portions of the video frame which is not part of the feature.
#     4.10) Resolution must be within 0.2% of the original aspect ratio.
#         4.10.1) The original aspect ratio must only be calculated from the source after cropping.
#         4.10.2) In situations where the source aspect ratio is incorrect as a result of bad mastering, a source sample and
#                 comparison screenshot of the final aspect ratio must be included.
#     4.11) Sample aspect ratio (SAR):
#           SAR = (PixelHeight / PixelWidth) / (DARHeight / DARWidth)
#     4.12) Display aspect ratio (DAR):
#           DAR = (PixelWidth * DARWidth) / (PixelHeight * DARHeight)
#     4.13) Display resolution:
#           DisplayWidth = PixelWidth * (SARWidth / SARHeight)
#     4.14) Aspect ratio (AR) error:
#           Original AR = (SourceWidth - [CropLeft + CropRight]) / (SourceHeight - [CropTop + CropBottom])
#           Release AR = EncodeWidth / EncodedHeight
#           AR Error % = [(Original AR - Release AR) / Original AR] * 100
#     4.15) Target resolution when resizing to maintain mod2 and reduce AR error:
#           TargetHeight = TargetWidth / [(SourceWidth - [CropLeft + CropRight]) / (SourceHeight - [CropTop + CropBottom])]
#           The correct mod2 value can also be calculated from the ceiling of TargetHeight if the value is odd, and the floor of
#           TargetHeight if the value is even.
#         4.15.1) Alternatively, the following can be used to confirm the correct resolution is used from the above method by
#                 calculating the upper and lower integer limit of TargetHeight:
#                 HeightA = floor(TargetHeight + (TargetHeight mod2))
#                 HeightB = floor(TargetHeight - (TargetHeight mod2))
#                 The TargetHeight value (HeightA or HeightB) which results in an aspect ratio error which tends to zero must be
#                 used.
#                 e.g. TargetWidth: 1280.
#                      SourceWidth: 1920, SourceHeight: 1080.
#                      CropLeft + CropRight = 0, CropTop + CropBottom = 4.
#                      TargetHeight = 1280 / ((1920 - 0) / (1080 - 4)) or 717.33.
#                      HeightA = floor(717.33 + (717.33 mod2)) or 718.
#                      HeightB = floor(717.33 - (717.33 mod2)) or 716.
#                      TargetWidth x HeightA = 1280x718 with -0.09% AR error.
#                      TargetWidth x HeightB = 1280x716 with 0.19% AR error.
#                      -0.09% tends closer to zero than 0.19% does (0.09 < 0.19), therefore, HeightA must be used.

# 5) [ Filters ]
#     5.1) Inverse telecine (IVTC), de-interlacing, or decimation must be applied as required.
#     5.2) Only the following smart deinterlacers can be used: QTGMC (with preset slow or better) or Nnedi3.
#     5.3) Only the following accurate field matching filters may be used: TIVTC or Decomb.
#     5.4) Only the following sharp resizers can be used: Spline36Resize, Spline64Resize or BlackmanResize.
#     5.5) Only frame accurate input source plugins can be used such as: DGIndex, DGDecNV or LSMASHSource. Use of frame
#          inaccurate input source filters (e.g. DirectShowSource) is not allowed.
#     5.6) Use of destructive and effects filters including, but not limited to: RemoveGrain, GrainFactory3, MedianBlur,
#          FineSharp are not allowed.
#     5.7) Optional recommended filtering methods:
#         5.7.1) Sources that require crop, and are not mod2 on opposing sides, can be avoided by moving the video by one pixel.
#                e.g. 139 pixels can be cropped from the top and bottom of a source.
#                     source = LSMASHVideoSource("source.mkv")
#                     Overlay(source, source, 0, -1)
#                     Crop(0, 138, 0, -140)
#         5.7.2) Use of SelectRangeEvery() as a quick method to test whether a higher or lower CRF value should be used.
#                e.g. SelectRangeEvery(3000, 150).
#         5.7.3) Selective debanding with f3kdb on scenes that require it is recommended, high attention to detail and caution
#                must be observed.

# 6) [ Framerate ]
#     6.1) Constant frame rate (CFR) must be used.
#         6.1.1) Variable frame rate (VFR) methods are not allowed.
#     6.2) Dupes based on frame rate are not allowed, use INTERNAL.
#     6.3) Features which contain a constant dupe sequence must be decimated.
#          e.g. A silent movie at 1080p24 with a dupe sequence of 1-in-6 must be decimated to 20 fps.
#     6.4) For sources which contain footage at varying frames per second throughout (hybrid sources), applying an inverse
#          telecine is left to the discretion of the group. The NFO must list a reason as per the final decision chosen.
#         6.4.1) It is assumed that the majority of the feature contains enough unique frames to not require an inverse telecine
#                filter. If it can be proven an inverse telecine or decimating filter does not result in any loss of unique
#                frames, this is considered a technical flaw.
#                e.g. The feature is filmed at 29.970 fps, but contains some footage filmed at 23.976 fps. Choosing to encode
#                     the entire release at 29.970 is valid.
#     6.5) Native and converted frame rates refer to the standard in which the feature was produced.
#         6.5.1) NTSC produced content is native to NTSC.
#         6.5.2) PAL produced content is native to PAL.
#         6.5.3) NTSC produced content that is mastered in PAL is considered as converted video.
#         6.5.4) PAL produced content that is mastered in NTSC is considered as converted video.
#     6.6) Sources which contain converted video must be restored to the original frame rate.
#         6.6.1) Converted video includes, but is not limited to: ghosted, blended, or duplicate frames.
#         6.6.2) Converted video does not include NTSC to PAL or PAL to NTSC sources which are sped up or slowed down.
#         6.6.3) If the restoration process is successful in restoring the footage to the native format without significant
#                issues or artifacts, the CONVERT tag must not be used.
#         6.6.4) In situations where the footage cannot be restored to the native format or results in significant issues or
#                artifacts, the CONVERT tag must be used.
#     6.7) True 50 / 59.940 fps video must be released at 50 / 59.940 fps. True 25 / 29.970 fps video released at 50 / 59.940
#          fps is not allowed and considered a technical flaw.
#         6.7.1) In cases of varying framerates of 25 / 29.970 fps and true 50 / 59.940 fps, the framerate of the main feature
#                must be used. e.g. studio for talk shows, game coverage for sports.
#         6.7.2) In rare situations, 25 / 50 fps sources must be restored to 23.976 or 29.97 fps.
#         6.7.3) In rare situations, 29.97 / 59.940 fps sources must be restored to 25 fps.

# 7) [ Video Codec ]
#     7.1) Video must be:
#         7.1.1) H.265/MPEG-H HEVC encoded with x265 10-bit for 720p/1080p HDR and 2160p SDR/HDR content.
#         7.1.2) H.264/MPEG-4 AVC encoded with x264 8-bit for 720p and 1080p SDR content.
#         7.1.3) Custom builds of x264/x265 are allowed and must be based off the current x264/x265 codebase. e.g. tMod, kMod.
#     7.2) x264/x265 headers must remain intact and must not be modified or removed.
#     7.3) x264/x265 must be kept up to date, with a maximum allowance, or grace period, of 60 days before groups are required
#          to update to the latest revision.
#         7.3.1) The official x264 git repository is the only reference for determining the current revision:
#                https://code.videolan.org/videolan/x264/tree/stable
#         7.3.2) The official x265 git repository is the only reference for determining the current revision:
#                https://bitbucket.org/multicoreware/x265/wiki/Home
#             7.3.2.1) Until such a time as MulticoreWare implement official revisional building, 3rd party builds (e.g. self-
#                      compiles, http://msystem.waw.pl/x265 or https://builds.x265.eu) can be used and must be kept up to date
#                      respecting 7.3.
#         7.3.3) The 60 day grace period must only be applied at pre time, not the tagged encoded date.
#         7.3.4) The grace period is only applicable to the revision preceding the latest update and does not reset active grace
#                periods of preceding revisions.
#                e.g. 2016-01-01: Revision A is used.
#                     2016-01-02: Revision B is committed, 60-day grace period begins for revision A.
#                     2016-01-05: Revision C is committed, 60-day grace period begins for revision B.
#                     2016-03-02: Revision A is no longer allowed, Revision B or C may be used.
#                     2016-03-05: Revision B is no longer allowed, Revision C must be used.
#     7.4) Segmented encoding is not allowed.
#     7.5) Constant Rate Factor (--crf) must be used.
#         7.5.1) Decimal values may be used.
#         7.5.2) Starting with an initial value of 16 or 14 (for especially compressible sources) for 2160p and 17 for 720p and
#                1080p is recommended.
#     7.6) While the encoded video stream bitrate exceeds x percent (where x is defined below) of the source video stream
#          bitrate, the CRF value must be incremented by 1 or 0.1, until it does not.
#         7.6.1) 30% for 720p.
#         7.6.2) 60% for 1080p.
#         7.6.3) 70% for 2160p.
#     7.7) Use of 2-pass is accepted for all resolutions. However, this method should be used only in extreme cases and not as a
#          primary replacement for CRF methods. e.g. If the source contains an excessive amount of grain or black and white
#          scenes.
#         7.7.1) The NFO must provide sufficient detailed evidence of 2-pass producing a visual improvement, bitrate or file
#                size advantage over CRF in regards to the source used.
#                e.g. Source has heavy grain throughout, which required the use of 2-pass to remain transparent at a reasonable
#                     bitrate. Included in the proof directory is test encodes of some troublesome areas at CRF and 2-pass
#                     showing a substantial improvement in quality at a more reasonable bitrate. CRF needs 6.5GB to stay
#                     transparent 2-pass only needed 4GB is detailed evidence.
#                e.g. The source was grainy so 2-pass was used is NOT detailed evidence.
#         7.7.2) Exceeding CRF 24 on any resolution is a good indication to consider the use of 2-pass.
#         7.7.3) 2-pass encodes must follow the percentage values in 7.6, it is recommended to target the maximum value allotted
#                and work down.
#     7.8) Exceeding the percentage values in 7.6 is allowed, but very detailed justification must be included in the NFO.
#          e.g. 720p encoded at CRF 13 resulting in an encode 50% of the source, this value was picked as the sourced content
#               had a lot of strobing effects (e.g. 1m10s-15m30s) and confetti scenes (e.g. 20m55s-50m60s) which compressed
#               poorly and required a higher bitrate to maintain transparency. Proof directory contains samples of these
#               troublesome scenes at 30% and 50% showing a substantial picture improvement.
#     7.9) Using unreasonably high CRF values or low target bitrates with 2-pass for the source content is considered a
#          technical flaw.
#          e.g. Producing a 1080p encode at 50% of the source bitrate, offering no justification in the NFO and having poor
#               transparency to the source IS a technical flaw.
#          e.g. Producing a 1080p encode at 30% of the source bitrate (This may occur on animation content to avoid a bloated
#               encode), offering justification in the NFO and having good transparency to the source is NOT a technical flaw.
#     7.10) Encoded video bitrate must not exceed the source video bitrate.
#         7.10.1) Video bitrate refers only to the bitrate for the video stream, and not the overall muxed bitrate of all
#                 streams within the container.
#         7.10.2) The following algorithm can also be used to estimate a CRF value if the value originally used results in a
#                 bitrate which exceeds the source's.
#                 ValidCRF = [-6 * (DestinationBitrate - ExcessiveBitrate) / ExcessiveBitrate] + CRFUsed
#                 e.g. Source bitrate: 4,500Kbps
#                      Target bitrate: ~3,400Kbps
#                      Encoded bitrate @ CRF17: 5,900Kbps
#                      ValidCRF = (-6 * (3400 - 5900) / 5900) + 17
#     7.11) Settings cannot go below what is specified for preset (--preset) 'slower' for x264 or 'slow' for x265 by the
#           revision used.
#     7.12) Level (x264: --level, x265: --level-idc) must be:
#         7.12.1) '4.1' for 720p
#         7.12.2) '4.1' for 1080p, '4.2' for 1080p above 30fps
#         7.12.3) '5.1' for 2160p, '5.2' for 2160p above 30fps.
#     7.13) Custom matrices are not allowed.
#     7.14) Zones (--zones) may be used, but should be used sparingly with a high degree of caution, the NFO must provide
#           sufficient detailed evidence for each zone used.
#           e.g. Used a zone at CRF 13 between frames 1634-5343 due to confetti spam and heavy motion resulting in very poor
#                compressibility. Proof directory contains two samples of this scene with and without the use of the zone
#                showing a drastic improvement in quality while still keeping a reasonable file size.
#     7.15) GPU offloading or any other forms of acceleration (e.g. --opencl, nvenc) is not allowed.
#     7.16) Optional tuning (--tune) parameters allowed are: 'film', 'grain', or 'animation'.
#     7.17) Optional settings recommended for tuning per source, see forum.doom9.org for further information:
#         7.17.1) For complex video, --preset veryslow is encouraged.
#         7.17.2) --aq-mode 3 --aq-strength x.x
#                 0.5-0.7 for grainy films.
#                 0.6-0.9 for digital films.
#                 0.9-1.1 for animation.
#         7.17.3) --psy-rd x.x:0.0
#                 0.8-1.2 for films.
#                 0.5-0.8 for animation.
#         7.17.4) --deblock x:x
#                 -3:-3 for films.
#                 1:1 for animation.
#     7.18) Sample Aspect Ratio (--sar) must be '1:1' (square).
#     7.19) Disabling deblocking (--no-deblock) is not allowed.
#     7.20) Frame rate must be passed to x264/x265 such that the keyframe interval (--keyint) and minimum GOP length
#           (--min-keyint) can be correctly set by the encoder. Changing these values is not allowed.
#     7.21) Color space must be 4:2:0.
#     7.22) Color matrix (--colormatrix) may be optionally set to 'bt709' for SDR content, but is not required.
#     7.23) x265 specifics:
#         7.23.1) Range (--range), color primaries (--colorprim), transfer (--transfer), color matrix (--colormatrix) and chroma
#                 sample location (--chromaloc) must be set to the same value as the source, or omitted if the source value is
#                 undefined.
#         7.23.2) Ultra-HD Bluray support (--uhd-bd) is not allowed.
#         7.23.3) High tier (--high-tier), repeat headers (--repeat-headers), access unit delimiter (--aud) and HRD signalling
#                 (--hrd) must be enabled.
#         7.23.4) HDR releases must be encoded with:
#             7.23.4.1) HDR10 signalling (--hdr10) and HDR10 optimization (--hdr10-opt) enabled.
#             7.23.4.2) Master Display (--master-display) and Max CL (--max-cll) set to the same value as the source, or omitted
#                       if the source value is undefined.
#                 7.23.4.2.1) Master Display and Max CL values must be taken from the whole concatenated source, not a partial
#                             source. e.g. the first m2ts file.
#     7.24) Any form of tone-mapping (e.g. HDR to SDR, DV to SDR, HDR10Plus to SDR) is not allowed, use INTERNAL.
#     7.25) HDR, DV and HDR10Plus must only be released at the source resolution, except in cases when 4.5.3 applies.
#           e.g. Source is 2160p and may only be released at 2160p, not 1080p or 720p.
#           e.g. Source is 1080p and may only be released at 1080p, not 720p.
#     7.26) Suggested command line:
#         7.26.1) x264 --preset slower --level ## --crf ##
#             7.26.1.1) Optional tweaks: --no-mbtree --no-fast-pskip --no-dct-decimate
#         7.26.2) x265 --high-tier --repeat-headers --aud --hrd --preset slow --level-idc ## --crf ## --range ## --colorprim ##
#                 --transfer ## --colormatrix ## --chromaloc ##
#             7.26.2.1) If HDR append: --hdr10 --hdr10-opt --master-display ## --max-cll ##
#             7.26.2.2) Optional tweaks: --no-cutree --no-open-gop --no-sao --pmode --aq-mode 4

# 8) [ Audio ]
#     8.1) Lossless tracks include, but are not limited to: DTS:X, TrueHD Atmos, DTS-HD MA, TrueHD, LPCM.
#     8.2) Lossy tracks include, but are not limited to: DTS-HD HR, E-AC3, DTS-ES, DTS, AC3.
#     8.3) Audio tracks must be:
#         8.3.1) For 1080p and 2160p releases:
#             8.3.1.1) The highest quality lossless track, in the order of preference specified in 8.1.
#             8.3.1.2) In cases where a lossless track is not present, the highest quality lossy track in the order of
#                      preference specified in 8.2.
#         8.3.2) For 720p releases:
#             8.3.2.1) AC3 or E-AC3 extracted core from a lossless or lossy track.
#             8.3.2.2) Lossless tracks must take priority when selecting which audio track is used. Lossy tracks must not be
#                      used to extract the core if there is a lossless track present.
#             8.3.2.3) In situations where the extracted core is below 640 Kbps, a new audio track must be transcoded to E-AC3
#                      or AC3 from the original lossless source track, see 9.6.
#                      e.g. Extracted core: AC3 @ 448 Kbps. = 448 Kbps < 640 Kbps, therefore a new audio track must be
#                           transcoded from the source track.
#             8.3.2.4) In situations where there is only a lossy track not in the AC3 or E-AC3 codec, a new audio track must be
#                      transcoded from it.
#                      e.g. Source track: DTS 1509 Kbps = No lossless track is available, DTS != AC3, therefore a new audio
#                           track must be transcoded from the source track.
#                      e.g. Source track: AC3 640 Kbps = No lossless track is available, no transcoding is required, mux as is.
#                      e.g. Source track: E-AC3 448 Kbps = No lossless track is available, upscaling bitrate is not allowed, no
#                           transcoding is required, mux as is.
#             8.3.2.5) In situations where there is only a lossy track in the AC3 or E-AC3 codec, they must be muxed as is.
#         8.3.3) All resolutions: FLAC must be used for lossless mono and lossless stereo tracks, as well as multi-channel LPCM
#                tracks, see 9.7.
#     8.4) Sync must not drift during the entire release.
#     8.5) Glitching or unrelated audio that occurs in any audio channel present (e.g. L, R, C) is considered a technical flaw.
#         8.5.1) Glitching is defined as, but not limited to: an audible glitch, missing audio, pops or clicks as a result of
#                encoding, unintended gaps within playback, missing dialogue, muted or muffled audio.
#     8.6) An English spoken release must only contain a single English dialogue track.
#         8.6.1) Except in situations of a remastered/restored source, whereby both original and remastered/restored audio track
#                may be muxed in. It is at the discretion of the group which track is chosen as the primary dialogue track.
#     8.7) A non-English spoken release may contain a secondary dialogue track.
#         8.7.1) The original audio track must be used and forced English subtitles must be present, see 10.2.
#         8.7.2) Secondary dubbed tracks must only be different dialects or varieties of the original language or an English
#                dub.
#                e.g. Original Spanish with secondary Latin Spanish.
#                e.g. Original French with secondary English dub.
#         8.7.3) In rare cases, a third dubbed track may be included for another dialect or variety of the original language,
#                accompanied with an English dubbed track.
#                e.g. Chinese original language, English dubbed track and a Cantonese dubbed track.
#     8.8) Non-English spoken releases which use only a dubbed track must be tagged as DUBBED.
#     8.9) Commentary audio may be included, see 9.8.
#     8.10) Audio tracks must only be included once at the highest level of quality allowed for that resolution. e.g. Including
#           an English dialogue track at lossless DTS-HD and lossy AC3 is not allowed.
#         8.10.1) This does not apply to embedded cores in lossless tracks, which are broken out by muxers as additional tracks,
#                 see 9.2.
#     8.11) Including additional special audio tracks (e.g. isolated scores, original mixes, different narrators) is allowed.
#     8.12) Supplementary audio tracks must have the title field set to a descriptive name. e.g. original, remastered,
#           commentary with director.
#     8.13) The correct ISO 639 language code supported by MKVToolnix must be set for all audio tracks.
#         8.13.1) In situations where the language is not supported by MKVToolnix, 'und' must be used.
#     8.14) Dupes based on multiple audio tracks, audio format, different narrators or remastered audio are not allowed, use
#           INTERNAL.
#     8.15) Using multiple retail audio sources of the same movie is allowed, each source and what content came from which must
#           be noted in the NFO.
#           e.g. Video from BluRay, dubbed track from DVD.

# 9) [ Audio Codec ]
#     9.1) Segmented encoding is not allowed.
#     9.2) When transcoding is not required, audio tracks have to be kept in the original format including any cores and muxed
#          as is.
#     9.3) Audio must not be resampled and must be kept in the original format of the source, e.g. 48 KHz for 48 KHz sources, 24
#          bit for 24 bit sources.
#     9.4) Audio must not have gain levels (normalization) adjusted and must be kept at the same levels as the source.
#     9.5) Audio must not have channels altered or removed and must be kept at the same channel count and layout as the source.
#          e.g. dual mono stays dual mono, mono stays mono, stereo stays stereo, 5.1 stays 5.1
#         9.5.1) Except for commentary audio, see 9.8.2.
#         9.5.2) Except when transcoding to AC3, see 9.6.2.
#     9.6) AC3 or E-AC3 must be used when transcoding from a lossless or lossy track.
#         9.6.1) AC3 or E-AC3 bitrate must not be below 640 Kbps, and must be created from a higher bitrate source. Only the
#                following methods are allowed (in order of preference):
#             9.6.1.1) Dolby Media Encoder
#             9.6.1.2) eac3to: -640
#             9.6.1.3) FFmpeg: -b:a 640k
#         9.6.2) When transcoding, positional audio metadata (e.g. DTS:X, TrueHD Atmos) and channels above 5.1 (e.g. 7.1) can be
#                retained at the discretion of the group.
#     9.7) FLAC must be used for lossless mono and lossless stereo tracks, as well as multi-channel LPCM tracks.
#         9.7.1) The best compression (level 8, --compression-level-8) must be used.
#         9.7.2) Replay-gain values (--replay-gain) must not be applied.
#     9.8) VBR AAC LC (Low Complexity) must be used for commentary audio.
#         9.8.1) Apple/QAAC, FDK-AAC or Nero must be used.
#         9.8.2) Audio with more than two channels must be down-mixed to stereo. Only the following methods are allowed (in
#                order of preference):
#             9.8.2.1) eac3to: -downStereo
#             9.8.2.2) FFMpeg: -ac 2
#         9.8.3) Quality based VBR encoding must be used; targeted or constrained VBR must not be used. Only the following
#                methods are allowed (in order of preference):
#             9.8.3.1) QAAC: --tvbr 82 --quality 2
#             9.8.3.2) FDK-AAC: --bitrate-mode 4 --profile 2
#             9.8.3.3) Nero: -q 0.4

# 10) [ Subtitles ]
#     10.1) All PGS subtitles (.sup) present on the source must be included as is.
#         10.1.1) It is at the discretion of the group to include forced subtitles for dubbed audio tracks not included in the
#                 release.
#     10.2) Features with foreign dialogue or overlays must include a separate SubRip subtitle (.srt) track for forced English
#           subtitles set as forced and default.
#         10.2.1) Except in situations where the source video stream contains hardcoded subtitles for non-English dialogue and
#                 overlays.
#         10.2.2) Except for features with excessive positional subtitles (e.g. Anime) which cannot be presented well in SubRip
#                 format. PGS subtitles must be used instead and set as forced and default.
#     10.3) Forced SubRip subtitles must be free of technical flaws. Including, but not limited to: sync issues, spelling,
#           incorrect OCR.
#         10.3.1) SubRip subtitles must be carefully OCR'd.
#         10.3.2) Minor errors in grammar or punctuation which do not change the meaning of the sentence are tolerated. However,
#                 it is recommended all errors be corrected.
#     10.4) Subtitles from an officially licenced (e.g. Netflix, MoviesAnywhere, HBO TV, Starz TV) WEB/HDTV source or
#           alternative retail disc of the same content are allowed.
#         10.4.1) Subtitles included from another source must be noted in the NFO. The source and which subtitle tracks used
#                 must be mentioned.
#         10.4.2) Fan-made or custom subtitles are not allowed.
#     10.5) Hardcoded subtitles which are only present in the source video stream are allowed, with the exception of non-English
#           hardcoded subtitles in English features.
#         10.5.1) When hardcoded subtitles extend over the entire feature, it must be tagged as SUBBED.
#                 e.g. English hardcoded subtitles throughout entire feature = Tag SUBBED
#                 e.g. English hardcoded subtitles for foreign dialogue only = Do not tag SUBBED
#         10.5.2) Subtitles which are only present within the letterboxed matte (i.e. the black borders) of a video frame must
#                 be cropped and OCR'd to SubRip format.
#         10.5.3) In situations where subtitles overlay active video and letterbox matte, cropping must be to the widest frame
#                 where the subtitles are present and applied equally to the relevant sides of the video frame.
#     10.6) Subtitles, unless otherwise stated, are not subject to propers or nukes for any technical flaws that may be present
#           in the track.
#     10.7) Dupes based on subtitles are not allowed, use INTERNAL.

# 11) [ Subtitle Format ]
#     11.1) Allowed formats are PGS (.sup) and SubRip (.srt).
#         11.1.1) Compression must only be used when muxing PGS subtitles, zlib is the only allowed compression algorithm.
#         11.1.2) PGS subtitles must not be resized.
#         11.1.3) UTF-8 encoding must be used for SubRip subtitle tracks.
#         11.1.4) SubRip subtitles are not allowed in 3D releases.
#     11.2) Subtitles must:
#         11.2.1) Have the correct ISO 639 language code supported by MKVToolNix set
#             11.2.1.1) In situations where the language is not supported by MKVToolNix, 'und' must be used.
#         11.2.2) Not be set as default or forced, unless otherwise stated in section 10.
#         11.2.3) Have the correct sync offset set during muxing.
#     11.3) It is strongly recommended to have descriptive names set on the title field.
#           e.g. Director's Commentary, English (Forced), English (SDH).
#     11.4) 3D releases must use 3D subtitles. Using 2D subtitles for a 3D release or vice versa is not allowed.
#     11.5) Burning-in subtitles to the video stream is not allowed.
#     11.6) External subtitles located in 'Subs' directories are not allowed.

# 12) [ Container ]
#     12.1) Container must be Matroska (.mkv). MKVToolnix is the recommended muxer.
#         12.1.1) Custom muxing tools are allowed. However, the output must adhere to the Matroska specifications and must
#                 retain identical compatibility with demuxers as files created with MKVToolnix.
#     12.2) Support for file streaming and playback from RAR is mandatory.
#     12.3) Matroska header compression must not be enabled.
#     12.4) Chapters are mandatory, when present on the source.
#         12.4.1) Chapter names are optional, but any chapter names including those auto-generated by muxers must be in English.
#     12.5) Watermarks, intros, outros or any other forms of defacement in any track (e.g. video, audio, subtitles, chapters)
#           are not allowed.

# 13) [ Packaging ]
#     13.1) Releases must be packed with RAR files and broken into a maximum of 101 volumes.
#         13.1.1) The old style extension-based naming scheme must be used. i.e. .rar to .r99.
#         13.1.2) The extension of the first volume in the archive set must be .rar.
#     13.2) RAR5/RARv5.0 is not allowed. RAR3/v2.0 or RAR4/v2.9 must be used.
#         13.2.1) Custom RAR tools can be used. Files produced from custom tools must adhere to the RAR3/v2.0 or RAR4/v2.9
#                 archive specification and retain identical compatibility with extractors and demuxers as file created with
#                 WinRAR/rar.
#     13.3) The following archive sizes are allowed:
#         13.3.1) Positive integer multiples of 50,000,000 bytes.
#                 e.g. (50 * 10^6) * n bytes, where n > 0.
#                      (50 * 10^6) * 4 bytes, 100,000,000 bytes, 400,000,000 bytes.
#         13.3.2) Releases must have a minimum of 10 volumes before the next multiple of 50,000,000 bytes is used.
#                 e.g. 10 volumes at 50,000,000 bytes can be repackaged to 5 volumes at 100,000,000 bytes.
#                      5 volumes at 100,000,000 bytes cannot be repacked to 4 volumes at 150,000,000 bytes.
#     13.4) A single SFV must be present for the primary archives and contain the entire archive set.
#     13.5) NFO, RAR, SFV, Proof, Sample files must have unique, lower-case filenames with the group tag.
#         13.5.1) Group tags must be unique to each group, and may be an abbreviated variation of the group name.
#     13.6) Preing a release with missing RAR(s) or SFV on all sites is considered a technical flaw.
#     13.7) Corrupt RAR(s) (errors upon extraction) is considered a technical flaw.
#     13.8) RAR compression and recovery records are not allowed.
#     13.9) Encryption or password protection is not allowed.
#     13.10) RAR archive set must only contain a single mkv file, any other files (e.g. multiple mkv files, txt files) are not
#            allowed.
#         13.10.1) Except for extras releases, multiple mkv files are allowed and filenames must be unique and descriptive.
#                  e.g. The.Big.Bang.Theory.S01.EXTRAS.1080p.BluRay.x264-GROUP contains:
#                       - Interview.with.the.Cast.mkv
#                       - S01E01.Bloopers.mkv
#             13.10.1.1) All HD/UHD extras must be included.
#             13.10.1.2) External extras located in 'Extras' directories are not allowed.

# 14) [ NFO ]
#     14.1) A single NFO file must be present, and must contain the following information:
#         14.1.1) Movies: iMDB link mandatory if available.
#         14.1.2) Series: TVmaze/TheTVDB link mandatory if available.
#             14.1.2.1) iMDB link is mandatory if it's available and TVmaze/TheTVDB links are not.
#             14.1.2.2) AniDB link may be used in lieu of a TVmaze/TheTVDB link for anime titles.
#         14.1.3) All content: Source video stream bitrate.
#             14.1.3.1) Must be retrieved using an accurate method, such as: MediaInfo (using --parsespeed=1), BDInfo, etc.
#     14.2) The following information is optional, but recommended:
#         14.2.1) Release name and group.
#         14.2.2) Release date.
#         14.2.3) Runtime.
#         14.2.4) Resolution and aspect ratio.
#         14.2.5) Frame rate.
#         14.2.6) Audio format.
#         14.2.7) File size.
#         14.2.8) Archive information.
#         14.2.9) List of included subtitles.
#         14.2.10) CRF value.

# 15) [ Proof ]
#     15.1) Proof must be provided for every release.
#         15.1.1) A photograph of reasonable high quality of the printed side of the physical disc with the group name clearly
#                 visible must be used.
#         15.1.2) Photographs must be at least 640x480px in resolution. Disc details must be clear and legible.
#         15.1.3) Small identifiable or sensitive information may be redacted.
#         15.1.4) Photographs must be of the actual disc used for the final encode.
#         15.1.5) Cover scans or m2ts samples may be included, but do not count as the required proof.
#     15.2) Proof must be placed in a separate directory named 'Proof'.
#         15.2.1) Proof must be in JPEG or PNG format and must not be archived.
#     15.3) When video, audio or subtitles are taken from multiple retail sources, proof must be provided for all sources used.
#           e.g. Video from Source A and audio from Source B are used. Proof of Source A and B is required.
#     15.4) All EXIF data (especially any personally identifiable such as geolocation) must be stripped.
#         15.4.1) Drawing attention (e.g. nuking, propering, mentioning in nfo) to proof which has not stripped EXIF data is
#                 strictly not allowed.
#     15.5) A release which fails to pre with the required proof is considered technically flawed and can be propered.
#         15.5.1) Proof fixes must be pred within 24 hours of the original pre.
#         15.5.2) Fixes provided after a proper has been released, or after 24 hours has elapsed from the original pre will not
#                 be accepted.

# 16) [ Samples / Source Samples ]
#     16.1) Releases must include a 50-70 second sample for each release, samples must:
#         16.1.1) Be placed in a separate directory named 'Sample'.
#         16.1.2) Be cut from the final video, not encoded separately and not be archived.
#         16.1.3) Not contain opening (e.g. studio titles) or closing (e.g. credits) footage when possible. e.g. cut samples
#                 from at least 2m in or the middle to avoid this.
#     16.2) Source samples are required for any release where the validity of the source may be brought into question.
#         16.2.1) Included source samples must have a unique filename and be placed within the 'Proof' directory.
#         16.2.2) If there is a question as to the validity of a source, encoding methods, or filters used; the release may be
#                 nuked within 24 hours of pre requesting a source sample and must include the initial suspicion or reason.
#                 e.g. source.sample.requested_suspicion.of.invalid.decimation.
#         16.2.3) Requests may mention a specific timecode to verify the sample provided is the same source used for the encode
#                 in question.
#                 e.g. include.ghosting.at.2m22s.
#         16.2.4) The group has 48 hours from the first nuke to pre a source sample that is at least 30 seconds and no more than
#                 5 minutes in length. If no specific timestamp is requested, source samples must be of the main feature and not
#                 the starting or ending credits.
#         16.2.5) Source samples must be packed as per section 13 and use the SOURCE.SAMPLE tag.
#         16.2.6) Failing to provide source proof, or providing insufficient proof to disprove any claims, the original release
#                 must remain nuked and can be considered technically flawed.

# 17) [ Tagging ]
#     17.1) The following source tags are allowed:
#           BLURAY, CAM, D-THEATER, DCP, HDDVD, MBLURAY, MUSE-LD, SCREENER, TELECINE, TELESYNC, UHD.BLURAY, UHD.MBLURAY,
#           WORKPRINT
#     17.2) Only the following additional tags are allowed:
#           ALTERNATIVE.CUT, BW, CHRONO, COLORIZED, CONVERT, DC, DIRFIX, DUBBED, DV, EXTENDED, EXTRAS, FS, HDR, HDR10Plus,
#           INTERNAL, LINE, NFOFIX, OAR, OM, PROOFFIX, PROPER, PURE, RATED, READNFO, REAL, REMASTERED, REPACK, RERIP, RESTORED,
#           SAMPLEFIX, SDR, SOURCE.SAMPLE, SUBBED, THEATRICAL, UNCENSORED, UNCUT, UNRATED, WS
#         17.2.1) <VERSION / CUT TITLE> may be used when a tag from 17.2 does not fit.
#                 e.g. Deadpool 2: The Super Duper Cut may be tagged as Deadpool.2.2018.The.Super.Duper.Cut
#         17.2.2) Proof must be provided for all remastered/restored releases to prove it is in fact a remaster/restore. At
#                 least 3 screenshots comparing the new and old sources/encodes must be included in the 'Proof' directory.
#                 Additional information should be included in the NFO, such as a link to an official source with details of the
#                 remaster/restore process.
#     17.3) Variations of any additional tag are not allowed.
#           e.g. READ.NFO or RNFO is not allowed, READNFO must be used.
#     17.4) READNFO should be used sparingly. Discretion is recommended.
#         17.4.1) The READNFO tag must not be used with PROPER, REPACK, or RERIP.
#     17.5) Tags must be grouped together, period-delimited, and follow the mandatory directory format, see rule 18.4.
#           e.g. EXTENDED.RERIP, REMASTERED.REPACK.
#     17.6) Tags must only be used once, but the order is left to the discretion of the group.
#         17.6.1) Except in situations where the REAL tag is required to be stacked to differentiate between multiple invalid
#                 releases.
#                 e.g. A REAL.REAL.PROPER is required for a REAL.PROPER and PROPER.
#     17.7) The HDR tag should only be used when there was an SDR release first and vice versa.
#           e.g. An SDR release of Gemini Man pred first, a subsequent HDR release must be tagged as such.
#           e.g. An HDR release of Star Wars pred first, a subsequent SDR release must be tagged as such.

# 18) [ Directory ]
#     18.1) Acceptable characters allowed for directories are:
#           ABCDEFGHIJKLMNOPQRSTUVWXYZ
#           abcdefghijklmnopqrstuvwxyz
#           0123456789._-
#     18.2) Single punctuation must be used. Consecutive punctuation is not allowed.
#           e.g. Show----Name.S01E01, Show.Name....S01E01
#     18.3) Typos or spelling mistakes in the directory are not allowed.
#     18.4) Releases must match the following directory format:
#         18.4.1) Feature.Title.<YEAR>.<TAGS>.[LANGUAGE].<RESOLUTION>.<FORMAT>.<x264|x265>-GROUP
#         18.4.2) Weekly.TV.Show.[COUNTRY_CODE].[YEAR].SXXEXX[Episode.Part].[Episode.Title].<TAGS>.[LANGUAGE].<RESOLUTION>.
#                 <FORMAT>.<x264|x265>-GROUP
#         18.4.3) Weekly.TV.Show.Special.SXXE00.Special.Title.<TAGS>.[LANGUAGE].<RESOLUTION>.<FORMAT>.<x264|x265>-GROUP
#         18.4.4) Multiple.Episode.TV.Show.SXXEXX-EXX[Episode.Part].[Episode.Title].<TAGS>.[LANGUAGE].<RESOLUTION>.<FORMAT>.
#                 <x264|x265>-GROUP
#         18.4.5) Cross.Over.TV.Show.One.SXXEXX[Episode.Part].[Episode.Title]_Show.Two.SXXEXX[Episode.Part].[Episode.Title].
#                 <TAGS>.[LANGUAGE].<RESOLUTION>.<FORMAT>.<x264|x265>-GROUP
#         18.4.6) Miniseries.Show.PartX.[Episode.Title].<TAGS>.[LANGUAGE].<RESOLUTION>.<FORMAT>.<x264|x265>-GROUP
#         18.4.7) Musical.Performance.or.Event.<PERFORMANCE_YEAR>.<TAGS>.<RESOLUTION>.<FORMAT>.<x264|x265>-GROUP
#         18.4.8) Artist.Name.Recording.Name.<RECORDING_YEAR>.<TAGS>.<RESOLUTION>.PURE.<FORMAT>.<x264|x265>-GROUP
#     18.5) Named directory arguments formatted inside <> must be included. Optional arguments formatted inside [] can be used
#           in some cases.
#         18.5.1) Mini-series parts must be at least 1 integer wide, and values used may extend past 9.
#                 e.g. Miniseries.Part.1, Miniseries.Part.10.
#         18.5.2) Episode and seasonal numbering must be at least 2 integers wide, and values used may extend past 99.
#                 e.g. S01E99, S01E100, S101E01.
#         18.5.3) Episode part refers to episodes, usually cartoons or animation, which split episodes into stories by different
#                 directors. Episode parts must be alphanumeric (A-Z, a-z, 0-9).
#                 e.g. The first episode from Season 2 of SpongeBob SquarePants is split into S02E01A/B, see:
#                      https://goo.gl/CVGXKu
#         18.5.4) Season must be omitted if a series is not a mini-series and does not have seasons.
#                 e.g. One Piece must be tagged as One.Piece.E01.
#         18.5.5) Episode title is optional.
#         18.5.6) Tags refers to all permitted tags only, see section 17.
#         18.5.7) Non-English releases must include the language tag. English releases must not include the language tag.
#             18.5.7.1) Language tags must be the full name of the language. Abbreviations or language codes are not allowed.
#                       e.g. FRENCH, RUSSIAN, GERMAN.
#         18.5.8) Format refers to the video source used.
#                 e.g. BluRay, TELECINE, HDDVD.
#     18.6) Do not indicate the ripping, or encoding methods that were used. Use the NFO for any technical details.
#     18.7) Non-series releases (e.g. movies, documentaries) must include the production year.
#     18.8) Different shows with the same title produced in different countries must have the ISO 3166-1 alpha 2 country code in
#           the show name.
#         18.8.1) Except for UK shows, which must use UK, not GB.
#         18.8.2) This rule does not apply to an original show, only shows that succeed the original.
#                 e.g. The.Office.S01E01 and The.Office.US.S01E01.
#     18.9) Different shows with the same title produced in the same country which begin in different years must have the year
#           of the first season in the directory.
#         18.9.1) The year is not required for the show broadcasted first.
#                 e.g. Second.Chance.S01E01 and Second.Chance.2016.S01E01.
#     18.10) Different shows with the same titles produced in the same country which begin in different years must have the
#            ISO-3166-1 alpha 2 country code followed by the year of the first season in the directory.
#         18.10.1) See rules 18.8 and 18.9 for country code and year explanations.
#                  e.g. Wanted.S01E01 (2005), Wanted.AU.S01E01 (2013), Wanted.AU.2016.S01E01 (2016).
#     18.11) Show names which are hyphenated or include punctuation must follow the format shown in the title sequence or
#            credits of the first episode, limited to the list of acceptable characters.
#         18.11.1) If no title card exists, see rule 18.13.1.
#         18.11.2) Additional titles and names given to an individual season must not be used.
#                  e.g. Archer.Vice.S05, Strike.Back.Legacy.S05.
#         18.11.3) Acronyms which show the ellipsis of letters with non-standard characters must be replaced with a period.
#                  e.g. M*A*S*H must be M.A.S.H.
#                  e.g. George Carlin... It's Bad for Ya! must be George.Carlin.Its.Bad.For.Ya.
#     18.12) Directory nomenclature and numbering must remain consistent across the lifetime of an individual show or event.
#         18.12.1) Shows which contain acronyms or secondary titles must follow the format used by the first release.
#                  e.g. Law.and.Order.SVU.S01E01 is the standard format that must be used for all following episodes,
#                       Law.and.Order.Special.Victims.Unit.S01E02 is not allowed.
#                       Shadowhunters.The.Mortal.Instruments.S01E01 is the standard format, Shadowhunters.S01E02 is not allowed.
#         18.12.2) Shows which air with extended content under modified names must use the primary show name and numbering with
#                  the EXTENDED tag.
#                  e.g. QI.S06E01 and QI.XL.S01E01, must be tagged as QI.S06E01 and QI.S06E01.EXTENDED respectively.
#                       Room.101.S01E01 and Room.101.Extra.Storage.S01E01, must be tagged as Room.101.S01E01 and
#                       Room.101.S01E01.EXTENDED respectively.
#         18.12.3) Groups cannot change the directory format of a show after a second release or episode with the same format
#                  exists.
#                  e.g. 2016-01-01: Law.and.Order.SVU.S01E01 sets the format.
#                       2016-01-08: Law.and.Order.SVU.S01E02 continues the format.
#                       2016-01-09: Law.and.Order.Special.Victims.Unit.S01E01.DIRFIX is not valid as the second episode already
#                  exists and continues with the previously defined format.
#         18.12.4) Except in situations where the show has an official change in its name, whereby all official references by
#                  the broadcaster or studio are of the new name. This change must be mentioned in the first NFO with the new
#                  name with relevant references.
#                  e.g. Gold.Rush.Alaska.S01E01 changed to Gold.Rush.S02E01.
#         18.12.5) Official name changes for a show does not include the renaming of individual seasons. Seasonal name changes
#                  must be ignored.
#                  e.g. Power.Rangers.S01 and Power.Rangers.S07 must be used. Power.Rangers.Lost.Galaxy.S07 must not be used.
#                       Strike.Back.S03, Strike.Back.S05 must be used. Strike.Back.Vengeance.S03, Strike.Back.Legacy.S05 must
#                       not be used.
#         18.12.6) Any deviations or changes require sufficient evidence listed in the NFO as to the reason for change.
#     18.13) User-contributed services such as TVMaze or TheTVDB must not be used as a reference when naming and numbering
#            episodes. It may be used as a general guide; however, official guides must be used.
#         18.13.1) The following order must be used as the primary source for naming and numbering.
#             18.13.1.1) Official website of the show.
#             18.13.1.2) Order and format listed by the original broadcaster.
#             18.13.1.3) Network guide.
#         18.13.2) In situations where official sources have inconsistent listings, or offer none at all, previously established
#                  numbering must be used.
#                  e.g. MythBusters, National Geographic Special Episodes.

# 19) [ Fixes ]
#     19.1) The following fixes are allowed:
#           DIRFIX, NFOFIX, PROOFFIX, SAMPLEFIX.
#     19.2) Any other form of fix is not allowed.
#           e.g. RARFIX, SFVFIX, SUBFIX
#     19.3) All fixes require an NFO and must state which release is being fixed.
#     19.4) A proper may not be released for a flaw which can be fixed with the above methods, with the exception of proof
#           fixes, see 15.5.1.
#     19.5) If multiple releases from a single season require a DIRFIX, a single DIRFIX per season is allowed and recommended.
#           e.g. Show.Name.S01.1080p.DIRFIX.BluRay.x264-GROUP.
#         19.5.1) If a single DIRFIX is used, all relevant releases and corresponding fixes must be listed in the NFO.
#                 e.g. The NFO should contain the following:
#                      This is the correct order in which to watch the show;
#                      Some.Show.S01E02.720p.BluRay.x264-GROUP is actually E01
#                      Some.Show.S01E01.720p.BluRay.x264-GROUP is actually E02
#                      Some.Show.S01E03.720p.BluRay.x264-GROUP
#                      Some.Show.S01E05.720p.BluRay.x264-GROUP is actually E04
#                      Some.Show.S01E04.720p.BluRay.x264-GROUP is actually E05
#                      Some.Show.S01E06.720p.BluRay.x264-GROUP

# 20) [ Dupes ]
#     20.1) All high definition formats are considered of equal quality and dupe each other, e.g. BluRay dupes HDDVD.
#         20.1.1) Except in situations where the release is a different version
#                 (e.g. DC, REMASTERED, ALTERNATIVE.CUT) or framed in a different way (e.g. WS, OM, OAR, FS) to the previous
#                 release, and is not censored after uncensored.
#     20.2) Native video streams do not dupe converted video streams.
#     20.3) Converted video streams dupe native video streams.
#     20.4) Releases which use retail sources do not dupe releases with non-retail sources.
#     20.5) Releases which use non-retail sources dupe retail releases.
#     20.6) Releases with muxed-in subtitles do not dupe releases with hardcoded subtitles.
#     20.7) Releases with hardcoded subtitles (i.e. SUBBED) dupe releases with muxed in subtitles.
#     20.8) HDR after SDR or vice versa does not dupe.
#     20.9) Non-foreign tagged English release does not dupe foreign tagged release.

# 21) [ Propers / Repacks / Re-Rips ]
#     21.1) Detailed reasons must be included in the NFO for all repacks, rerips, and propers.
#         21.1.1) Proper reasons must be clearly stated in the NFO, including timestamps and specifics in regards to the flaw
#                 when appropriate.
#         21.1.2) If a release is not globally nuked, a sample demonstrating the flaws in the original release is required, and
#                 must be placed within the 'Proof' directory.
#     21.2) Propers are only permitted in the case of a technical flaw in the original release.
#         21.2.1) Qualitative propers are not allowed, use INTERNAL.
#     21.3) Audio or visual glitches can be propered with a release which does not exhibit the same flaw.
#         21.3.1) In situations where mastering issues results in visual or audio glitches, a release must not be nuked until a
#                 valid proper, repack, or rerip using a glitch-free source or master is released.
#     21.4) RERIP must be used for ripping or encoding issues.
#     21.5) REPACK must be used for packing or muxing issues.

# 22) [ Internals ]
#     22.1) Unless explicitly stated, internal releases must follow all rules detailed in this document. Internal releases are
#           only exempt from the following rules:
#         22.1.1) Encoding specifics, e.g. experimental settings, advanced settings.
#         22.1.2) Experimental codecs or containers.
#     22.2) Internal releases must mention what rule exemptions have been observed with reasoning in the NFO, and may be nuked
#           if they do not.
#           e.g. Tone-mapped to SDR from HDR UHD.Bluray as there is no planned SDR disc for this feature.
#         22.2.1) In situations where something was not mentioned in the NFO, groups may provide an NFOFIX to avoid or reverse a
#                 nuke.
#     22.3) Using DIRFIX.INTERNAL to avoid a nuke is not allowed, and must be nuked fix.for.nuke.

# 23) [ Ruleset Specifics ]
#     23.1) This ruleset is to be considered the ONLY official ruleset for HD and UHD retail. It supersedes all previous
#           revisions, rulesets and precedents.
#         23.1.1) Releasing under former rulesets or codecs is not allowed, and must be nuked defunct.ruleset or defunct.codec.
#         23.1.2) The naming standards listed in this document must only take effect once a current running season has ended.
#                 Any existing naming schemes must be used in the event of missing episode(s) from older seasons being filled.
#         23.1.3) This ruleset is not retroactive, and only applies to releases released under it.
#     23.2) The following definition of keywords throughout this ruleset are as follows:
#         23.2.1) Must: the rule is explicit in the definition and is compulsory.
#         23.2.2) Should: implies the rule is a suggestion, and is non-compulsory.
#         23.2.3) Can or may: implies the rule is optional, and is non-compulsory.
#         23.2.4) e.g: refers to common examples, elements listed should not be considered as all possibilities.
#         23.2.5) i.e: refers to the only examples, elements listed will be considered as all valid possibilities.

# 24) [ Notes ]
#     24.1) The inclusion of 2-pass in this ruleset should not be misconstrued as preferring it for every release, CRF must
#           always be considered the primary method. Instead, it is encouraged for groups to use 2-pass methods for rare cases
#           when files provided are of extremely high quality.
#         24.1.1) Video which contains an excessive amount of noise may often result in an unnecessary large bitrate. In such
#                 situations, encoding to a smaller bitrate using 2-pass can result in a file size improvement with negligible
#                 loss in video quality.
#     24.2) Dolby Vision (DV) and HDR10+ (HDR10Plus) are considered out of scope, due to lack of support and no standard
#           workflow for producing them, and must only be released as INTERNAL.
#         24.2.1) DV encodes must have DV Profile (--dolby-vision-profile) and RPU metadata (--dolby-vision-rpu) set to the same
#                 values as the source.
#             24.2.1.1) Including the DV enhancement layer on a HDR or HDR10Plus encode is another option.
#             24.2.1.2) Until such a time as Matroska gains support for Dolby Vision, MP4 may be used and dlb_mp4base or MP4Box
#                       are the only allowed muxers. It is fully at the group's discretion to work around any pitfalls of the
#                       MP4 container (e.g. limited audio codec and subtitles support). Groups are exempt from any rules with
#                       regards to these pitfalls.
#         24.2.2) HDR10Plus releases, in addition to HDR specifics (see 7.23.4), must have SEI tone mapping metadata
#                 (--dhdr10-info) set to the same values as the source. Tone mapping metadata optimisation (--dhdr10-opt) must
#                 be enabled.
#         24.2.3) Any metadata must be extracted from the whole concatenated source, not a partial source. e.g. the first m2ts
#                 file.
#         24.2.4) Until such a time as mapping metadata to cropped encodes is possible, DV and HDR10Plus are exempt from
#                 cropping rules and must be left uncropped.
#         24.2.5) The rules below will apply in a hypothetical future when all pitfalls and issues mentioned above are resolved,
#                 support has become widespread, does not result in any playback issues and at least three months have elapsed
#                 from support being added.
#             24.2.5.1) If the source contains a DV enhancement layer, it must be muxed in with the correct DV Profile set for
#                       the source during muxing.
#             24.2.5.2) If the source contains HDR10Plus SEI metadata, 24.2.2 is mandatory.
#             24.2.5.3) 24.2.3 must be respected.
#             24.2.5.4) The HDR10Plus tag must not be used.
#             24.2.5.5) DV single layer encodes (see 24.2.1) are only allowed when the source is single layer DV (i.e. No HDR,
#                       only DV). The DV tag must only be used in the case of single layer DV.
#     24.3) Until such a time as remuxed releases have their own ruleset. They are subject to relevant rules from sections
#           12-24, of this ruleset.
#         24.3.1) Remuxed releases must include all subtitle tracks and all audio tracks (e.g. commentary, dialogue) only once
#                 at the highest quality available on the source. It is at the discretion of the group to include dubbed
#                 language or descriptive tracks.
#         24.3.2) Tracks must be muxed in as is without any modification.
#         24.3.3) When including optional Dolby Vision enhancement layers in a remux, 24.3.1.1 must be followed.
#         24.3.4) When tagging remuxed releases, the following applies to section 18.
#             24.3.4.1) H265 must be used in place of X265.
#             24.3.4.2) H264 must be used in place of X264.

# [ Signed (in alphabetical order) - 85 Groups ]
# aAF, AMIABLE, ANiHLS, ARCHiViST, BALKAN, BARGAiN, BATV, BEDLAM, BiPOLAR, BLOW, BRMP, CADAVER, CAPRiCORN, Chakra, CiNEFiLE,
# CONDITION, Counterfeit, CREEPSHOW, DAA, DEATH, DEFLATE, DEPTH, DEV0, DoNE, EiDER, ELBOWDOWN, EMERALD, Felony, FLAME,
# FUTURiSTiC, GeTiT, GHOULS, GiMCHi, GreenBlade, GxP, HAiDEAF, HAiKU, HDEX, HFPA, IAMABLE, IcHoR, iNGOT, JRP, KYR, LATENCY,
# LiBRARiANS, LiQUiD, LOUNGE, MBLURAYFANS, MUSiCBD4U, NODLABS, OUIJA, PAST, PHASE, PRESENT, PSYCHD, PURELiQUiD, REACTOR,
# RedBlade, REGRET, Replica, REWARD, SADPANDA, SAPHiRE, SCOTLUHD, SECTOR7, SH0W, SHORTBREHD, SiNNERS, SNOW, SPECTACLE, SPOOKS,
# TAXES, TOPAZ, TREBLE, TURBO, URANiME, USURY, ViRGO, W4F, WEST, WhiteRhino, WUTANG, YELLOWBiRD, YOL0W

# [ Refused to Sign (in alphabetical order) - 8 Groups ]
# AAA, AAAUHD, DODELIJK, GUACAMOLE, KWANGMYONG, MAYHEM, TURMOiL, WATCHABLE

# [ Revisions ]
# 2007-04-28 - High.Def.x264.movie.standards.rls.1-NFO
# 2007-07-05 - High.Def.x264.Movie.Standards.Rev2
# 2008-10-13 - High.Definition.x264.Standards.Revision.3.0-HDX
# 2008-12-20 - High.Definition.x264.Standards.Revision.3.1-HDX
# 2009-01-27 - High.Definition.x264.Standards.Revision.3.1.Addendum.1-HDX
# 2011-01-29 - High.Definition.x264.Standards.Revision.4.0-HDX
# 2011-01-29 - High.Definition.x264.Standards.Revision.4.0.UPDATE-HDX
# 2020-04-15 - High.Definition.x264.and.Ultra.High.Definition.x265.Standards.Revision.5.0-HDX - Total rewrite, hardened all
# rules, switched to CRF, UHD and x265 are supported.
