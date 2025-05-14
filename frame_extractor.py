import cv2
import os
import argparse
import time

def process_video(video_path, output_dir):

    if not os.path.isfile(video_path) or not video_path.lower().endswith(('.mp4', '.avi', '.mov')):
        print(f"Invalid video file: {video_path}")
        return


    try:
        os.makedirs(output_dir, exist_ok=True)
        test_file = os.path.join(output_dir, 'permission_test.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
    except PermissionError:
        print(f"Permission denied for output directory: {output_dir}")
        return

    vid = cv2.VideoCapture(video_path)
    if not vid.isOpened():
        print(f"Error opening video: {video_path}")
        return
    
    start_time = time.time()
    fps = vid.get(cv2.CAP_PROP_FPS)
    frame_interval = max(1, int(fps / 60))
    total_frames = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))
    
    frame_count = 0
    saved_count = 0
    timestamps = []
    last_reported = 0

    while True:
        ret, frame = vid.read()
        if not ret:
            break

        current_ts = vid.get(cv2.CAP_PROP_POS_MSEC)

        if frame_count % frame_interval == 0:
            output_path = os.path.join(output_dir, f"frame_{saved_count:05d}.jpg")
            

            max_retries = 3
            for attempt in range(max_retries):
                success = cv2.imwrite(output_path, frame)
                if success:
                    timestamps.append(current_ts)
                    saved_count += 1
                    break
                print(f"Attempt {attempt+1}/{max_retries} failed for frame {frame_count}")
            else:
                print(f"Permanently failed to save frame {frame_count}")


        if frame_count > 0:
            elapsed = time.time() - start_time
            fps_actual = frame_count / elapsed
            remaining = (total_frames - frame_count) / fps_actual
            progress = int((frame_count / total_frames) * 100)
            
            if progress >= last_reported + 5:
                print(f"Processing: {progress}% completed | "
                      f"Elapsed: {elapsed:.1f}s | "
                      f"Remaining: {remaining:.1f}s | "
                      f"FPS: {fps_actual:.1f}")
                last_reported = progress

        frame_count += 1

    vid.release()
    

    if timestamps:
        ts_path = os.path.join(output_dir, "timestamps.csv")
        with open(ts_path, 'w') as f:
            f.write("frame_number,timestamp_ms\n")
            for i, ts in enumerate(timestamps):
                f.write(f"{i},{ts}\n")


    expected_frames = total_frames // frame_interval
    success_rate = saved_count/expected_frames if expected_frames > 0 else 0
    print(f"Successfully saved {saved_count}/{expected_frames} frames ({success_rate:.1%})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract 60 FPS frames from videos')
    parser.add_argument('--video-dir', default='.', help='Directory containing video files')
    args = parser.parse_args()
    
    for fname in os.listdir(args.video_dir):
        if fname.endswith('.mp4'):
            video_path = os.path.join(args.video_dir, fname)
            output_dir = os.path.join("output", fname[:-4])
            process_video(video_path, output_dir)