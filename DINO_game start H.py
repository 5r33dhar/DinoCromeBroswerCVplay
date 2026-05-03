#DinoCromeWwebdriver.py

import os
import time
import webbrowser
from selenium import webdriver
#from selenium.webdriver.common.keys import Keys
#from selenium.webdriver.common.by import By
import pyautogui
from mss import mss  # MSS library for fast screen capture


# Automated Dino Game Player using Computer Vision

import cv2  # OpenCV for image processing
import numpy as np  # NumPy for numerical array operations
import pyautogui  # PyAutoGUI to simulate keyboard presses
from mss import mss  # MSS library for fast screen capture

def DinoGame():
# def DinoGame(locx, locy, desired_width, desired_height):
        
        driver = webdriver.Chrome()
        # Initialize the Chrome WebDriver (make sure chromedriver is in your PATH)
        urls = r"chrome://dino"

    # # Open the Chrome Dinosaur game in the browser
        try:
             driver.get(urls)
        except:
        # Ignore the "Internet Disconnected" error 
        # because that's exactly what we want for the Dino game!
            pass
        time.sleep(2) # Give it a moment to open

        # Wait for the game to load and place the window in the correct position
        # driver.minimize_window()
        # driver.set_window_position(1200 , 528)
        # driver.set_window_size(800, 800)
        
        fw = pyautogui.getActiveWindow()

        if fw:
            fw.width = 900# Sets the width of the window to 1000 pixels.
            fw.height = 550# Sets the height of the window to 800 pixels.
            fw.topleft = (1000,  550) # Moves the window to the specified (x, y) coordinates on the screen.
            fw.activate() # Make sure it's focused
        
        # time.sleep(5)# Wait for user to switch to Chrome window
        # print(f"Active window fw.width: {fw.width }")
        # print(f"Active window fw.height: {fw.height}")


        time.sleep(2)
        pyautogui.press('space')
        time.sleep(2)# Wait for user to switch to Chrome window
        



# Method 1: Capture screen region using pyautogui (slower but reliable)
def capture_screen_region_opencv(x, y, desired_width, desired_height):
    """
    Captures a rectangular region from the screen using pyautogui.
    Args: x, y - top-left corner coordinates
        desired_width, desired_height - dimensions of capture region
    Returns: BGR format image array
    """
    screenshot = pyautogui.screenshot(region=(x, y, desired_width, desired_height))
    screenshot = np.array(screenshot)  # Convert to numpy array
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)  # Convert RGB to BGR for OpenCV
    return screenshot

# DinoGame(2880, 528, 1630, 800)
DinoGame() 
# fw = pyautogui.getActiveWindow()
# fw.width = 1630# Sets the width of the window to 1000 pixels.
# fw.height = 800# Sets the height of the window to 800 pixels.
# fw.topleft = (2880, 528) # Moves the window to the specified (x, y) coordinates on the


def pre_process(_imgCrop):
    """
    Preprocesses the cropped image to make obstacles easier to detect.
    Steps:
    1. Convert to grayscale
    2. Apply binary thresholding (inverted)
    3. Detect edges using Canny edge detection
    4. Dilate to make edges thicker and more visible
    """
    # Step 1: Convert color image to grayscale for easier processing
    gray_frame = cv2.cvtColor(_imgCrop, cv2.COLOR_BGR2GRAY)
    cv2.imshow("Game Gray", gray_frame)


    # Step 2: Apply binary thresholding (value > 127 becomes white, else black)
    # THRESH_BINARY_INV inverts the result (obstacles become white)
    _, binary_frame = cv2.threshold(gray_frame, 127, 255, cv2.THRESH_BINARY_INV)
    cv2.imshow("Game Binary", binary_frame)
    
    # Step 3: Apply Canny edge detection to find obstacle boundaries
    # Parameters (50, 50): lower and upper threshold for edge detection
    canny_frame = cv2.Canny(binary_frame, 50, 50)
    cv2.imshow("Game Canny", canny_frame)

    # Step 4: Dilate (expand) edges to make obstacles more visible and connected
    # Create a 5x5 kernel for dilation operation
    kernel = np.ones((5, 5))
    # Apply dilation 2 times to expand edges
    dilated_frame = cv2.dilate(canny_frame, kernel, iterations=2)
    cv2.imshow("Game Dilated", dilated_frame)
 
    return dilated_frame

def find_obstacles(_imgCrop, _imgPre):
    """
    Detects obstacles (contours) in the preprocessed image.
    Args: _imgCrop - original cropped image (for drawing contours)
          _imgPre - preprocessed image (for finding contours)
    Returns: imgContours - image with drawn contours
             conFound - list of detected contours with bounding box info
    """
    # Copy image to draw contours
    imgContours = _imgCrop.copy()

    # Detect contours (shapes/boundaries) from the preprocessed image
    # cv2.RETR_EXTERNAL → retrieves only outer contours (ignores inner ones)
    # cv2.CHAIN_APPROX_SIMPLE → compresses contour points to save memory
    # Find contours with minimum area of 100 pixels to filter out noise
    #imgContours, conFound = cv2.findContours(_imgCrop, _imgPre, cv2.CHAIN_APPROX_SIMPLE)
    contours, hierarchy = cv2.findContours(_imgPre, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # List to store all detected valid contours and their details
    conFound = []

    # Loop through each detected contour
    for cnt in contours:

        # Calculate area of the contour (number of pixels inside it)
        area = cv2.contourArea(cnt)

        # Ignore very small contours (noise)
        if area > 100:

            # Get bounding rectangle around contour
            # x, y → top-left corner
            # w, h → width and height
            x, y, w, h = cv2.boundingRect(cnt)

            # Store useful information about the contour
            conFound.append({
                "cnt": cnt,                          # actual contour points
                "area": area,                        # size of contour
                "bbox": (x, y, w, h),                # bounding box
                "center": (x + w // 2, y + h // 2)   # center point of box
            })

            # Draw the contour outline in green on the image
            cv2.drawContours(imgContours, [cnt], -1, (0, 255, 0), 2)

            # Draw bounding rectangle in blue
            cv2.rectangle(imgContours, (x, y), (x + w, y + h), (255, 0, 0), 2)

    # Return:
    # 1. Image with drawn contours
    # 2. List of contour data
    return imgContours, conFound


def game_logic(conFound, _imgContours, jump_distance=65):
    """
    Main game logic: detects closest obstacle and triggers jump action.
    Args: conFound - list of detected contours
          _imgContours - image to draw debug lines on
          jump_distance - pixel distance threshold to trigger jump (default: 65 pixels)
    Returns: _imgContours - updated image with debug visualization
    """
    if conFound:
        # Find the leftmost contour (closest to the dinosaur/player)
        # bbox[0] is the x-coordinate of the bounding box
        left_most_contour = sorted(conFound, key=lambda x: x["bbox"][0])

        # Draw a green line from the leftmost obstacle for visualization
        # This helps debug the detection
        cv2.line(_imgContours, (0, left_most_contour[0]["bbox"][1] + 10),
                 (left_most_contour[0]["bbox"][0], left_most_contour[0]["bbox"][1] + 10), (0, 200, 0), 10)



        # Check if the leftmost obstacle is within jump distance
        # If distance < 65 pixels, it's time to jump!
        if left_most_contour[0]["bbox"][0] < jump_distance:
            pyautogui.press("space")  # Press spacebar to make dinosaur jump
            print("jump")  # Print debug message
    return _imgContours



# Method 2: Capture screen region using MSS (faster than pyautogui)
def capture_screen_region_opencv_mss(x, y, width, height):
    """
    Captures a rectangular region from the screen using MSS library (faster).
    Args: x, y - top-left corner coordinates
          width, height - dimensions of capture region
    Returns: BGR format image array
    """
    with mss() as sct:
        # Define the monitor region to capture
        monitor = {"top": y, "left": x, "width": width, "height": height}
        screenshot = sct.grab(monitor)  # Grab the screen region
        # Convert to an OpenCV image array
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)  # Convert BGRA to BGR for OpenCV compatibility
        return img


while True:

    # ============= STEP 1: CAPTURE SCREEN =============
    # Capture the game region: starting at x=2880, y=528, width=1630, height=800

    # imgGame = capture_screen_region_opencv(2880, 528, 1630, 800)
    #imgGame = capture_screen_region_opencv(1000, 550, 900, 600)
    imgGame = capture_screen_region_opencv_mss(1000, 550, 900, 600)
    cv2.imshow("Game Vision", imgGame)


    # ============= STEP 2: CAPTURE SCREEN =============
     # Capture the Crop region: starting at x=350, y=450, start_col=10
        # This focuses on the area where obstacles appear
    cp = 365, 420, 150# These values define the cropping rectangle (top, bottom, start_col)
    imgCrop = imgGame[cp[0]:cp[1], cp[2]:]  # Extract the cropped region
    # Convert cropped image to binary and enhance edges for better detection
    cv2.imshow("Game TopCrop", imgCrop)

    # ============= STEP 3: PREPROCESS IMAGE =============
    # Convert cropped image to binary and enhance edges for better detection
    imgPre = pre_process(imgCrop)
    cv2.imshow("Game Preprocessed", imgPre)

    # ============= STEP 4: DETECT OBSTACLES =============
    # Find contours (obstacles) in the preprocessed image
    imgContours, conFound = find_obstacles(imgCrop, imgPre)   
    cv2.imshow("Game Contours", imgContours)
    print("imgContours is None?", imgContours)

    # ============= STEP 5: APPLY GAME LOGIC =============
    # Decide whether to jump based on obstacle proximity
    imgContours = game_logic(conFound, imgContours)
    cv2.imshow("Game Logic", imgContours)
    # This image will show the contours and the debug line indicating the closest obstacle


    print("cp:", cp)
    print("imgContours is None?", imgContours is None)
    #print("imgContours is None?", imgContours)# Check

    # ============= STEP 6: DISPLAY RESULTS =============
    # Replace the cropped region in original image with processed version
    imgGame[cp[0]:cp[1], cp[2]:] = imgContours
    cv2.imshow("Game Logic2", imgContours)

    # # Update FPS counter and add it to the display
    #fps, imgGame = fpsReader.update(imgGame)
    cap = cv2.VideoCapture(0)
    pTime = 0 # Previous time

    success, imgGame = cap.read()

    # Calculate FPS
    cTime = time.time() # Current time
    fps = 1 / (cTime - pTime)
    pTime = cTime

    # Display FPS on the image
    cv2.putText(imgGame, f'FPS: {int(fps)}', (20, 70), cv2.FONT_HERSHEY_PLAIN, 
                3, (255, 0, 0), 3)



    # # Display the final image with all annotations
    cv2.imshow("Game", imgGame)



     # Press 'q' in the CV2 window to stop the script
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    # cv2.waitKey(1)

cv2.destroyAllWindows()