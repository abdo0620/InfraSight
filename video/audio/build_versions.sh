#!/usr/bin/env bash
# Builds the three trailers with sound from the silent render (out/infrasight-trailer.mp4), without re-encoding the
# picture: Remotion renders each version's audio mix (src/audio/Soundtrack.tsx), ffmpeg normalises it to -14 LUFS
# (two passes, true peak -1.5 dB, so no clipping) and puts it next to the untouched video stream.
# Run from video/: bash audio/build_versions.sh [1 2 3]
set -e
cd "$(dirname "$0")/.."
BIN=node_modules/@remotion/compositor-win32-x64-msvc
[ -x "$BIN/ffmpeg.exe" ] || BIN=$(dirname "$(command -v ffmpeg)")
FFMPEG=$BIN/ffmpeg; [ -x "$FFMPEG.exe" ] && FFMPEG=$FFMPEG.exe
VIDEO=out/infrasight-trailer.mp4
declare -A NAME=([1]=trailer_1_no_music [2]=trailer_2_generated_music [3]=trailer_3_inspired_music [4]=trailer_4_streets_beat)
mkdir -p out/audio
VERSIONS=("$@"); [ ${#VERSIONS[@]} -eq 0 ] && VERSIONS=(1 2 3)
for v in "${VERSIONS[@]}"; do
  echo "== version $v: rendering the audio mix"
  npx remotion render Trailer "out/audio/mix_$v.wav" --codec=wav --props="{\"version\":$v}" --log=error
  echo "== version $v: measuring loudness"
  m=$("$FFMPEG" -hide_banner -i "out/audio/mix_$v.wav" -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
  get() { echo "$m" | sed -n "s/.*\"$1\" : \"\([^\"]*\)\".*/\1/p"; }
  "$FFMPEG" -hide_banner -v error -y -i "out/audio/mix_$v.wav" \
    -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$(get input_i):measured_TP=$(get input_tp):measured_LRA=$(get input_lra):measured_thresh=$(get input_thresh):offset=$(get target_offset):linear=true,aresample=48000" \
    "out/audio/master_$v.wav"
  echo "== version $v: muxing with the video (video stream copied as is)"
  "$FFMPEG" -hide_banner -v error -y -i "$VIDEO" -i "out/audio/master_$v.wav" -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 256k \
    -shortest -movflags +faststart "out/${NAME[$v]}.mp4"
  echo "   out/${NAME[$v]}.mp4"
done
