# DinoCromeBroswerCVplay
This Python script is an automated bot designed to play the Chrome Dinosaur game 
Core Components:

Environment Setup (DinoGame):Uses Selenium to launch Chrome and navigate to chrome://dino.Uses PyAutoGUI to automatically resize and reposition the browser window to a specific location on the screen, ensuring the bot always knows where to look.

Screen Capture:Employs the MSS library, which is a ultra-fast cross-platform screen shooting module. This provides the low latency needed to react to obstacles at high game speeds.

Image Processing Pipeline (pre_process):
Grayscale Conversion: Simplifies the image data.Binary 
Thresholding: High-contrast filtering to separate obstacles from the background.
Canny Edge Detection: Outlines the shapes of cacti and pterodactyls.
Dilation: Thickens the edges to ensure the detection logic doesn't miss small or thin obstacles.

Object Detection (find_obstacles):
Uses OpenCV (cv2) to find "contours" (shapes) within the processed image.
Filters out small noise and calculates the "Bounding Box" (the rectangle surrounding an object) for every detected obstacle.

Decision Logic (game_logic):
The bot identifies the left-most obstacle (the one closest to the Dino).
It calculates the distance between the Dino and the obstacle.
When the obstacle enters a specific "danger zone" (the jump_distance threshold), the script triggers pyautogui.press('space') to make the Dinosaur jump.
