import {Config} from '@remotion/cli/config';

// codec and quality are passed by the npm scripts (video: h264 --crf=18; audio-only renders: wav, which takes no crf)
Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(92);
Config.setOverwriteOutput(true);
